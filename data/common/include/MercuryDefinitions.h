/*
 * MercuryDefinitions.h
 *
 *  Created on: Aug 11, 2020
 *      Author: Christian Angelsen, STFC DSSG
 */

#ifndef INCLUDE_MERCURYDEFINITIONS_H_
#define INCLUDE_MERCURYDEFINITIONS_H_

#define ILLEGAL_FEM_IDX -1

namespace Mercury {

    typedef struct MercurySensorLayoutMapEntry
    {
      int sensor_rows_;
      int sensor_columns_;

      MercurySensorLayoutMapEntry(int sensor_rows=ILLEGAL_FEM_IDX, int sensor_columns=ILLEGAL_FEM_IDX) :
        sensor_rows_(sensor_rows),
        sensor_columns_(sensor_columns)
      {};
    } MercurySensorLayoutMapEntry;

    const std::string default_sensors_layout_map = "2x2";

    // A Mercury sensor is 80x80 pixels
    static const uint16_t pixel_columns_per_sensor = 80;
    static const uint16_t pixel_rows_per_sensor =  80;

}

#endif /* INCLUDE_MERCURYDEFINITIONS_H_ */
