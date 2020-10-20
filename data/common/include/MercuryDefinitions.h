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

    static const size_t num_sensors = 2;
    typedef enum {
      sensorConfigUnknown = -1,
      sensorConfigOne = 0,      // 1 x 1 sensors
      sensorConfigTwo = 1       // 2 x 2 sensors
    } SensorConfigNumber;

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

    static const size_t primary_packet_size = 8000;
    static const size_t num_primary_packets[num_sensors] = {1, 6};
    static const size_t max_primary_packets = 6;
    static const size_t tail_packet_size[num_sensors]	= {4800, 3200};
    static const size_t num_tail_packets = 1;

    static const uint32_t start_of_frame_mask = 1 << 31;
    static const uint32_t end_of_frame_mask   = 1 << 30;
    static const uint32_t packet_number_mask  = 0x3FFFFFFF;

    typedef struct
    {
      uint32_t frame_counter;
      uint32_t packet_number_flags;
    } PacketHeader;

    typedef struct
    {
      uint32_t packets_received;
      uint8_t  sof_marker_count;
      uint8_t  eof_marker_count;
      uint8_t  packet_state[max_primary_packets + num_tail_packets];
    } FemReceiveState;

    typedef struct
    {
        uint32_t frame_number;
        uint32_t frame_state;
        struct timespec frame_start_time;
        uint32_t total_packets_received;
        uint8_t total_sof_marker_count;
        uint8_t total_eof_marker_count;
        uint8_t active_fem_idx;
        FemReceiveState fem_rx_state;
    } FrameHeader;

    inline const std::size_t num_fem_frame_packets(const SensorConfigNumber sensor_config)
    {
      std::size_t num_fem_frame_packets = (num_primary_packets[sensor_config] + num_tail_packets);
      return num_fem_frame_packets;
    }
}

#endif /* INCLUDE_MERCURYDEFINITIONS_H_ */
