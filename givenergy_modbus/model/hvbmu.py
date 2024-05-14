"""
High level interpretation of the HV Battery Module (BMU) modbus registers.

The BMU itself is the primary class; the others are
supporting enumerations.
"""

from .register import (
    Converter as DT,
    DynamicDoc,
    RegisterDefinition as Def,
    IR,
    RegisterGetter,
)

"""
Adder: 0x50~0x6F
Register start address = (Register base NO) + 120 *  (BAMS_Addr - 0x90)  * 32 + 120* (BCU_Addr - 0x70);
"""


class BMU(RegisterGetter, metaclass=DynamicDoc):
    # pylint: disable=missing-class-docstring
    # The metaclass turns accesses to __doc__ into calls to
    # _gendoc()  (which we inherit from RegisterGetter)

    _DOC = """Battery presents all battery attributes as python types."""

    REGISTER_LUT = {
        # Input Registers, block 60-119
        "v_cell_01": Def(DT.milli, None, IR(60)),
        "v_cell_02": Def(DT.milli, None, IR(61)),
        "v_cell_03": Def(DT.milli, None, IR(62)),
        "v_cell_04": Def(DT.milli, None, IR(63)),
        "v_cell_05": Def(DT.milli, None, IR(64)),
        "v_cell_06": Def(DT.milli, None, IR(65)),
        "v_cell_07": Def(DT.milli, None, IR(66)),
        "v_cell_08": Def(DT.milli, None, IR(67)),
        "v_cell_09": Def(DT.milli, None, IR(68)),
        "v_cell_10": Def(DT.milli, None, IR(69)),
        "v_cell_11": Def(DT.milli, None, IR(70)),
        "v_cell_12": Def(DT.milli, None, IR(71)),
        "v_cell_13": Def(DT.milli, None, IR(72)),
        "v_cell_14": Def(DT.milli, None, IR(73)),
        "v_cell_15": Def(DT.milli, None, IR(74)),
        "v_cell_16": Def(DT.milli, None, IR(75)),
        "v_cell_17": Def(DT.milli, None, IR(76)),
        "v_cell_18": Def(DT.milli, None, IR(77)),
        "v_cell_19": Def(DT.milli, None, IR(78)),
        "v_cell_20": Def(DT.milli, None, IR(79)),
        "v_cell_21": Def(DT.milli, None, IR(80)),
        "v_cell_22": Def(DT.milli, None, IR(81)),
        "v_cell_23": Def(DT.milli, None, IR(82)),
        "v_cell_24": Def(DT.milli, None, IR(83)),
        "t_cell_01": Def(DT.deci, None, IR(90)),
        "t_cell_02": Def(DT.deci, None, IR(91)),
        "t_cell_03": Def(DT.deci, None, IR(92)),
        "t_cell_04": Def(DT.deci, None, IR(93)),
        "t_cell_05": Def(DT.deci, None, IR(94)),
        "t_cell_06": Def(DT.deci, None, IR(95)),
        "t_cell_07": Def(DT.deci, None, IR(96)),
        "t_cell_08": Def(DT.deci, None, IR(97)),
        "t_cell_09": Def(DT.deci, None, IR(98)),
        "t_cell_10": Def(DT.deci, None, IR(99)),
        "t_cell_11": Def(DT.deci, None, IR(100)),
        "t_cell_12": Def(DT.deci, None, IR(101)),
        "t_cell_13": Def(DT.deci, None, IR(102)),
        "t_cell_14": Def(DT.deci, None, IR(103)),
        "t_cell_15": Def(DT.deci, None, IR(104)),
        "t_cell_16": Def(DT.deci, None, IR(105)),
        "t_cell_17": Def(DT.deci, None, IR(106)),
        "t_cell_18": Def(DT.deci, None, IR(107)),
        "t_cell_19": Def(DT.deci, None, IR(108)),
        "t_cell_20": Def(DT.deci, None, IR(109)),
        "t_cell_21": Def(DT.deci, None, IR(110)),
        "t_cell_22": Def(DT.deci, None, IR(111)),
        "t_cell_23": Def(DT.deci, None, IR(112)),
        "t_cell_24": Def(DT.deci, None, IR(113)),
        "serial_number": Def(
            DT.string, None, IR(114), IR(115), IR(116), IR(117), IR(118)
        ),
    }

    def is_valid(self) -> bool:
        """Try to detect if a battery exists based on its attributes."""
        return self.serial_number not in (
            None,
            "",
            " ",
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            "          ",
        )
