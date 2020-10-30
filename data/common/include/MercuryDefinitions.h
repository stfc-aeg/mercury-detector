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

    // A Mercury sensor is 80x80 pixels
    static const uint16_t pixel_columns_per_sensor = 80;
    static const uint16_t pixel_rows_per_sensor =  80;

    static const size_t primary_packet_size = 8000;
    static const size_t num_primary_packets = 1;
    static const size_t max_primary_packets = 6;
    static const size_t tail_packet_size= 4800;
    static const size_t num_tail_packets = 1;

    static const uint32_t start_of_frame_mask = 1 << 31;
    static const uint32_t end_of_frame_mask   = 1 << 30;
    static const uint32_t packet_number_mask  = 0x3FFFFFFF;

    static const int32_t default_frame_number = -1;

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

    inline const std::size_t num_fem_frame_packets()
    {
      std::size_t num_fem_frame_packets = (num_primary_packets + num_tail_packets);
      return num_fem_frame_packets;
    }

    inline const std::size_t frame_size()
    {
      std::size_t frame_size = (primary_packet_size * num_primary_packets) +
          (tail_packet_size * num_tail_packets);
      return frame_size;
    }

    inline const std::size_t max_frame_size()
    {
      std::size_t max_frame_size = sizeof(FrameHeader) + frame_size();
      return max_frame_size;
    }
}

#endif /* INCLUDE_MERCURYDEFINITIONS_H_ */
