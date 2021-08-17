/**
 * (C) Copyright 2021 Intel Corporation.
 *
 * SPDX-License-Identifier: BSD-2-Clause-Patent
 */

#ifndef __DAOS_PIPE_H__
#define __DAOS_PIPE_H__

#if defined(__cplusplus)
extern "C" {
#endif


/**
 * A filter part object, used to build a filter object for a pipeline.
 *
 */
typedef struct {
	/**
	 *  Part type can be any of the following:
	 *   -- function:
	 *      - logical functions:
	 *          DAOS_FILTER_FUNC_EQ:		==
	 *          DAOS_FILTER_FUNC_NE:		!=
	 *          DAOS_FILTER_FUNC_LT:		<
	 *          DAOS_FILTER_FUNC_LE:		<=
	 *          DAOS_FILTER_FUNC_GE:		>=
	 *          DAOS_FILTER_FUNC_GT:		>
	 *          DAOS_FILTER_FUNC_LIKE:		== (reg exp.)
	 *          DAOS_FILTER_FUNC_ISNULL:		==NULL
	 *          DAOS_FILTER_FUNC_ISNOTNULL:		!=NULL
	 *          DAOS_FILTER_FUNC_AND:		&&
	 *          DAOS_FILTER_FUNC_OR:		||
	 *      - aggeration functions:
	 *          DAOS_FILTER_FUNC_SUM:		SUM()
	 *          DAOS_FILTER_FUNC_MIN:		MIN()
	 *          DAOS_FILTER_FUNC_MAX:		MAX()
	 *          DAOS_FILTER_FUNC_AVG:		AVG()
	 *   -- key:
	 *          DAOS_FILTER_OID:	Filter part object represents object id
	 *          DAOS_FILTER_DKEY:	Filter part object represents dkey
	 *          DAOS_FILTER_AKEY	Filter part object represents akey
	 *   -- constant:
	 *          DAOS_FILTER_CONST:	Filter part object is a constant
	 */
	char		*part_type;
	/**
	 * Type of data. Only relevant for keys and constant filter part type
	 * objects:
	 *          DAOS_FILTER_TYPE_BINARY
	 *          DAOS_FILTER_TYPE_STRING
	 *          DAOS_FILTER_TYPE_INTEGER
	 *          DAOS_FILTER_TYPE_REAL
	 */
	char		*data_type;
	/**
	 * Number of operands for this filter part object. For example, for '=='
	 * we have 2 operands.
	 */
	uint32_t	num_operands;
	/**
	 * If filtering by akey, this tells us which one.
	 */
	d_iov_t		akey;
	/**
	 * How many constants we have in \a constant
	 */
	size_t		num_constants;
	/**
	 * This object holds the value of the constants
	 */
	d_iov_t		*constant;
	/**
	 * If filter should only be applied starting at an offset of the data.
	 */
	size_t		data_offset;
	/**
	 * Size of the data to be filtered.
	 */
	size_t		data_len;
} daos_filter_part_t;

/**
 * A filter object, used to build a pipeline.
 */
typedef struct {
	/**
	 * Filter type can be any of the following:
	 *   -- DAOS_FILTER_CONDITION:
	 *          Records in, and records (meeting condition) out
	 *   -- DAOS_FILTER_AGGREGATION:
	 *          Records in, a single value out
	 *
	 * NOTE: Pipeline nodes can only be chained the following way:
	 *             (condition) --> (condition)
	 *             (condition) --> (aggregation)
	 *             (aggregation) --> (aggregation)*
	 *
	 *       *chained aggragations are actually done in parallel. For
	 *        example, the following pipeline:
	 *            (condition) --> (aggregation1) --> (aggregation2)
	 *        is actually exectuted as:
	 *                          -> (aggregation1)
	 *            (condition) -|
	 *                          -> (aggregation2)
	 */
	char			*filter_type;
	/**
	 * Number of filter parts inside this pipeline filter
	 */
	size_t			num_parts;
	/**
	 * Array of filter parts for this filter object
	 */
	daos_filter_part_t	*parts;
} daos_filter_t;

/**
 * A pipeline.
 */
typedef struct {
	/**
	 * Version number of the data structure.
	 */
	uint64_t		version;
	/**
	 * Number of filters chained in this pipeline
	 */
	size_t			num_filters;
	/**
	 * Array of filters for this pipeline
	 */
	daos_filter_t		*filters;
} daos_pipeline_t;


/**
 * Adds a new filter object to the pipeline \a pipeline object. The effect of
 * this function is equivalent to "pushing back" the new filter at the end of
 * the pipeline.
 *
 * \param[in,out]	pipeline	Pipeline object.
 *
 * \param[in]		filter		Filter object to be added to the pipeline.
*/
int
daos_pipeline_add(daos_pipeline_t *pipeline, daos_filter_t *filter);

/**
 * Adds a new filter part object to the filter object \a filter. The effect of
 * this function is equivalent to "pushing back" the new filter part at the end
 * of the filter stack.
 *
 * \param[in,out]	filter	Filter object.
 *
 * \param[in]		part	Filter part object to be added to a filter.
 */
int
daos_filter_add(daos_filter_t *filter, daos_filter_part_t *part);

/**
 * Checks that a pipeline object is well built. If the pipeline object is well
 * built, the function will return 0 (no error).
 *
 * \param[in]		pipeline	Pipeline object.
 */
int
daos_pipeline_check(daos_pipeline_t *pipeline);

/**
 * Runs a pipeline on DAOS, returning objects and/or aggregated results.
 *
 * \params[in]		coh		Container open handle.
 *
 * \param[in]		oh		Optional object open handle.
 *
 * \param[in]		pipeline	Pipeline object.
 *
 * \param[in]		th		Optional transaction handle. Use
 *					DAOS_TX_NONE for an independent
 *					transaction.
 *
 * \param[in]		flags		Conditional operations.
 *
 * \param[in]		dkey		Optional dkey. When passed, no iteration
 *					is done and processing is only performed
 *					on this specific dkey.
 *
 * \param[in,out]	nr_iods		[in]: Number of I/O descriptors in the
 *					iods table.
 *					[out]: Number of returned I/O
 *					descriptors in the iods table.
 *
 * \param[in,out]	iods		[in/out]: Array of I/O descriptors. Each
 *					descriptor is associated with a given
 *					akey and describes the list of
 *					record extents to fetch from the array.
 *
 * \param[in,out]	anchor		Hash anchor for the next call, it should
 *					be set to zeroes for the first call, it
 *					should not be changed by caller
 *					between calls.
 *
 * \param[in,out]	nr_kds		[in]: Number of key descriptors in
 *					\a kds.
 *					[out:] Number of returned key descriptors.
 *
 * \param[in,out]	kds		[in]: Optional preallocated array of \nr
 *					key descriptors.
 *					[out]: Size of each individual key along
 *					with checksum type and size stored just
 *					after the key in \a sgl_keys.
 *
 * \param[out]		sgl_keys	Optional sgl storing all dkeys to be
 *					returned.
 *
 * \param[out]		sgl_recx	Optional sgl storing all the records to
 *					be returned. Allocated by the user, and
 *					array size has to be nr_kds*nr_iods.
 *
 * \param[out]		sgl_agg		Optional sgl with the returned value of
 *					the aggregator(s).
 *
 * \param[in]		ev		Completion event. It is optional.
 *					Function will run in blocking mode if
 *					\a ev is NULL.
 */
int
daos_pipeline_run(daos_handle_t coh, daos_handle_t *oh, daos_pipeline_t pipeline,
		  daos_handle_t *th, uint64_t flags, daos_key_t *dkey,
		  uint32_t *nr_iods, daos_iod_t *iods, daos_anchor_t *anchor,
		  uint32_t *nr_kds, daos_key_desc_t *kds, d_sg_list_t *sgl_keys,
		  d_sg_list_t *sgl_recx, d_sg_list_t *sgl_agg,
		  daos_event_t *ev);

#if defined(__cplusplus)
}
#endif

#endif /* __DAOS_PIPE_H__ */