#ifndef FRAMESIMULATOR_MERCURYFRAME_H
#define FRAMESIMULATOR_MERCURYFRAME_H

#include <vector>
#include <iostream>
#include <sstream>
#include <string>

#include "Packet.h"

namespace FrameSimulator {

    class MercuryFrameSimulatorPlugin;

    typedef std::vector<Packet> PacketList;

    /** MercuryFrame class
     *
     * An mercury frame and its packets; defines the SOF and EOF markers
     * for reading an mercury frame from a pcap file
     */

    class MercuryFrame {

        friend class MercuryFrameSimulatorPlugin;

    public:

        MercuryFrame(const int& frameNum);

    private:

        PacketList packets;

        int frame_number;
        int trailer_frame_num;
        std::vector<int> SOF_markers;
        std::vector<int> EOF_markers;

    };

}

#endif //FRAMESIMULATOR_MERCURYFRAME_H
