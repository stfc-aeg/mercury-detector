"""MERCURY ASIC register map.

This module implements a simple enumerated map of the SPI registers
of the MERCURY ASIC, linking the register names (as defined by the ASIC
documentation) with their addresses.

Tim Nicholls, STFC Detector Systems Software Group
"""
from enum import IntEnum


class RegisterMap(IntEnum):
    """
    MERCURY ASIC register map.

    This class enumerates the addresses of the SPI registers on the MERCURY ASIC.
    """

    # Page 1 registers

    # Config registers
    CONFIG1   = 0  # Configuration
    GLOB1     = 1  # Global select 1
    GLOB2     = 2  # Global select 2
    GLOB_VAL1 = 3  # Global config 1
    GLOB_VAL2 = 4  # Global config 2
    FRM_LNGTH = 5  # Frame length (clocks)
    INT_TIME  = 6  # Integration time (frames)
    TEST_SR   = 7  # Test shift registe config
    SER_BIAS  = 8  # Serialiser PLL bias
    TDC_BIAS  = 9  # TDC PLL bias

    # Timing Registers
    TDC_DATA_LD     = 10  # Read out data load on
    RST_PRE_ON      = 11  # Reset preamplifier on
    RST_PRE_OFF     = 12  # Reset preamplifier off
    CDS_PRE_ON      = 13  # Reset CDS amplifier on
    CDS_PRE_OFF     = 14  # Reset CDS amplifier off
    SAMPLE_C_ON     = 15  # CDS sample on
    SAMPLE_C_OFF    = 16  # CDS sample off
    SAMPLE_H_ON     = 17  # Sample & hold on
    SAMPLE_H_OFF    = 18  # Sample & hold off
    RAMP_EN_ON      = 19  # Ramp enable on
    RAMP_EN_OFF     = 20  # Ramp enable off
    TDC_OUT_EN_ON   = 21  # TDC output enable on
    TDC_OUT_EN_OFF  = 22  # TDC output enable off
    TDC_CNT_RST_ON  = 23  # TDC counter reset on
    TDC_CNT_RST_OFF = 24  # TDC counter reset off
    CAL_TOGGLE      = 25  # Calibration pulse toggle

    # Segment control
    SEG_CONTROL1_SER  = 26  # Segment1 control for serialiser
    SEG_CONTROL2_SER  = 27  # Segment2 control for serialiser
    SEG_CONTROL3_SER  = 28  # Segment3 control for serialiser
    SEG_CONTROL4_SER  = 29  # Segment4 control for serialiser
    SEG_CONTROL5_SER  = 30  # Segment5 control for serialiser
    SEG_CONTROL6_SER  = 31  # Segment6 control for serialiser
    SEG_CONTROL7_SER  = 32  # Segment7 control for serialiser
    SEG_CONTROL8_SER  = 33  # Segment8 control for serialiser
    SEG_CONTROL9_SER  = 34  # Segment9 control for serialiser
    SEG_CONTROL10_SER = 35  # Segment10 control for serialiser
    SEG_CONTROL1_EN   = 36  # Segment1 control for enables
    SEG_CONTROL2_EN   = 37  # Segment2 control for enables
    SEG_CONTROL3_EN   = 38  # Segment3 control for enables
    SEG_CONTROL4_EN   = 39  # Segment4 control for enables
    SEG_CONTROL5_EN   = 40  # Segment5 control for enables
    SEG_CONTROL6_EN   = 41  # Segment6 control for enables
    SEG_CONTROL7_EN   = 42  # Segment7 control for enables
    SEG_CONTROL8_EN   = 43  # Segment8 control for enables
    SEG_CONTROL9_EN   = 44  # Segment9 control for enables
    SEG_CONTROL10_EN  = 45  # Segment10 control for enables

    # Ramp control
    RAMP_CONTROL1   = 46  # Ramp bias control segment1 1,2
    RAMP_CONTROL2   = 47  # Ramp bias control segment1 3,4
    RAMP_CONTROL3   = 48  # Ramp bias control segment2 1,2
    RAMP_CONTROL4   = 49  # Ramp bias control segment2 3,4
    RAMP_CONTROL5   = 50  # Ramp bias control segment3 1,2
    RAMP_CONTROL6   = 51  # Ramp bias control segment3 3,4
    RAMP_CONTROL7   = 52  # Ramp bias control segment4 1,2
    RAMP_CONTROL8   = 53  # Ramp bias control segment4 3,4
    RAMP_CONTROL9   = 54  # Ramp bias control segment5 1,2
    RAMP_CONTROL10  = 55  # Ramp bias control segment5 3,4
    RAMP_CONTROL11  = 56  # Ramp bias control segment6 1,2
    RAMP_CONTROL12  = 57  # Ramp bias control segment6 3,4
    RAMP_CONTROL13  = 58  # Ramp bias control segment7 1,2
    RAMP_CONTROL14  = 59  # Ramp bias control segment7 3,4
    RAMP_CONTROL15  = 60  # Ramp bias control segment8 1,2
    RAMP_CONTROL16  = 61  # Ramp bias control segment8 3,4
    RAMP_CONTROL17  = 62  # Ramp bias control segment9 1,2
    RAMP_CONTROL18  = 63  # Ramp bias control segment9 3,4
    RAMP_CONTROL19  = 64  # Ramp bias control segment10 1,2
    RAMP_CONTROL20  = 65  # Ramp bias control segment10 3,4

    # Serialiser control
    SER_CONTROL1A  = 66   # Serialisers segment1 static controls A
    SER_CONTROL1B  = 67   # Serialisers segment1 static controls B
    SER_CONTROL1C  = 68   # Serialisers segment1 static controls C
    SER_CONTROL1D  = 69   # Serialisers segment1 static controls D
    SER_CONTROL1E  = 70   # Serialisers segment1 static controls E
    SER_CONTROL1F  = 71   # Serialisers segment1 static controls F
    SER_CONTROL2A  = 72   # Serialisers segment2 static controls A
    SER_CONTROL2B  = 73   # Serialisers segment2 static controls B
    SER_CONTROL2C  = 74   # Serialisers segment2 static controls C
    SER_CONTROL2D  = 75   # Serialisers segment2 static controls D
    SER_CONTROL2E  = 76   # Serialisers segment2 static controls E
    SER_CONTROL2F  = 77   # Serialisers segment2 static controls F
    SER_CONTROL3A  = 78   # Serialisers segment3 static controls A
    SER_CONTROL3B  = 79   # Serialisers segment3 static controls B
    SER_CONTROL3C  = 80   # Serialisers segment3 static controls C
    SER_CONTROL3D  = 81   # Serialisers segment3 static controls D
    SER_CONTROL3E  = 82   # Serialisers segment3 static controls E
    SER_CONTROL3F  = 83   # Serialisers segment3 static controls F
    SER_CONTROL4A  = 84   # Serialisers segment4 static controls A
    SER_CONTROL4B  = 85   # Serialisers segment4 static controls B
    SER_CONTROL4C  = 86   # Serialisers segment4 static controls C
    SER_CONTROL4D  = 87   # Serialisers segment4 static controls D
    SER_CONTROL4E  = 88   # Serialisers segment4 static controls E
    SER_CONTROL4F  = 89   # Serialisers segment4 static controls F
    SER_CONTROL5A  = 90   # Serialisers segment5 static controls A
    SER_CONTROL5B  = 91   # Serialisers segment5 static controls B
    SER_CONTROL5C  = 92   # Serialisers segment5 static controls C
    SER_CONTROL5D  = 93   # Serialisers segment5 static controls D
    SER_CONTROL5E  = 94   # Serialisers segment5 static controls E
    SER_CONTROL5F  = 95   # Serialisers segment5 static controls F
    SER_CONTROL6A  = 96   # Serialisers segment6 static controls A
    SER_CONTROL6B  = 97   # Serialisers segment6 static controls B
    SER_CONTROL6C  = 98   # Serialisers segment6 static controls C
    SER_CONTROL6D  = 99   # Serialisers segment6 static controls D
    SER_CONTROL6E  = 100  # Serialisers segment6 static controls E
    SER_CONTROL6F  = 101  # Serialisers segment6 static controls F
    SER_CONTROL7A  = 102  # Serialisers segment7 static controls A
    SER_CONTROL7B  = 103  # Serialisers segment7 static controls B
    SER_CONTROL7C  = 104  # Serialisers segment7 static controls C
    SER_CONTROL7D  = 105  # Serialisers segment7 static controls D
    SER_CONTROL7E  = 106  # Serialisers segment7 static controls E
    SER_CONTROL7F  = 107  # Serialisers segment7 static controls F
    SER_CONTROL8A  = 108  # Serialisers segment8 static controls A
    SER_CONTROL8B  = 109  # Serialisers segment8 static controls B
    SER_CONTROL8C  = 110  # Serialisers segment8 static controls C
    SER_CONTROL8D  = 111  # Serialisers segment8 static controls D
    SER_CONTROL8E  = 112  # Serialisers segment8 static controls E
    SER_CONTROL8F  = 113  # Serialisers segment8 static controls F
    SER_CONTROL9A  = 114  # Serialisers segment9 static controls A
    SER_CONTROL9B  = 115  # Serialisers segment9 static controls B
    SER_CONTROL9C  = 116  # Serialisers segment9 static controls C
    SER_CONTROL9D  = 117  # Serialisers segment9 static controls D
    SER_CONTROL9E  = 118  # Serialisers segment9 static controls E
    SER_CONTROL9F  = 119  # Serialisers segment9 static controls F
    SER_CONTROL10A = 120  # Serialisers segment10 static controls A
    SER_CONTROL10B = 121  # Serialisers segment10 static controls B
    SER_CONTROL10C = 122  # Serialisers segment10 static controls C
    SER_CONTROL10D = 123  # Serialisers segment10 static controls D
    SER_CONTROL10E = 124  # Serialisers segment10 static controls E
    SER_CONTROL10F = 125  # Serialisers segment10 static controls F

    # Shift registers
    SR_CAL  = 126  # Calibration shift register
    SR_TEST = 127  # Test shift register

    # Page 2 registers

    # NB addr 128,129 not used

    # Bias registers
    CHIP_BIAS  = 130  # Global chip bias
    SER_BIAS1  = 131  # Serialiser biassegment1
    SER_BIAS2  = 132  # Serialiser biassegment2
    SER_BIAS3  = 133  # Serialiser biassegment3
    SER_BIAS4  = 134  # Serialiser biassegment4
    SER_BIAS5  = 135  # Serialiser biassegment5
    SER_BIAS6  = 136  # Serialiser biassegment6
    SER_BIAS7  = 137  # Serialiser biassegment7
    SER_BIAS8  = 138  # Serialiser biassegment8
    SER_BIAS9  = 139  # Serialiser biassegment9
    SER_BIAS10 = 140  # Serialiser biassegment10

    # Read-only flag registers
    FIFO_FULL1    = 141  # FIFO full flags (8 to 1)
    FIFO_FULL2    = 142  # FIFO full flags (16 to 9)
    FIFO_FULL3    = 143  # FIFO full flags (20 to 17)
    SER_CLK_CHECK1 = 144  # Serialiser clock status flags (8 to 1)
    SER_CLK_CHECK2 = 145  # Serialiser clock status flags (16 to 9)

    @classmethod
    def size(cls):
        """Calculate the size of the register address space.

        This class method is used to determine the size of the register
        address space so the emulator can allocate appropriate storge.

        :return: size of the register address space
        """
        return max([item.value for item in cls])
