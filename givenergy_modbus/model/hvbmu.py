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

    def __init__(self, cache, offset):
        self.cache = cache
        self.offset = offset
        self.REGISTER_LUT = {
        # Input Registers, block 60-119
        "v_cell_01": Def(DT.milli, None, IR(60+(offset*120))),
        "v_cell_02": Def(DT.milli, None, IR(61+(offset*120))),
        "v_cell_03": Def(DT.milli, None, IR(62+(offset*120))),
        "v_cell_04": Def(DT.milli, None, IR(63+(offset*120))),
        "v_cell_05": Def(DT.milli, None, IR(64+(offset*120))),
        "v_cell_06": Def(DT.milli, None, IR(65+(offset*120))),
        "v_cell_07": Def(DT.milli, None, IR(66+(offset*120))),
        "v_cell_08": Def(DT.milli, None, IR(67+(offset*120))),
        "v_cell_09": Def(DT.milli, None, IR(68+(offset*120))),
        "v_cell_10": Def(DT.milli, None, IR(69+(offset*120))),
        "v_cell_11": Def(DT.milli, None, IR(70+(offset*120))),
        "v_cell_12": Def(DT.milli, None, IR(71+(offset*120))),
        "v_cell_13": Def(DT.milli, None, IR(72+(offset*120))),
        "v_cell_14": Def(DT.milli, None, IR(73+(offset*120))),
        "v_cell_15": Def(DT.milli, None, IR(74+(offset*120))),
        "v_cell_16": Def(DT.milli, None, IR(75+(offset*120))),
        "v_cell_17": Def(DT.milli, None, IR(76+(offset*120))),
        "v_cell_18": Def(DT.milli, None, IR(77+(offset*120))),
        "v_cell_19": Def(DT.milli, None, IR(78+(offset*120))),
        "v_cell_20": Def(DT.milli, None, IR(79+(offset*120))),
        "v_cell_21": Def(DT.milli, None, IR(80+(offset*120))),
        "v_cell_22": Def(DT.milli, None, IR(81+(offset*120))),
        "v_cell_23": Def(DT.milli, None, IR(82+(offset*120))),
        "v_cell_24": Def(DT.milli, None, IR(83+(offset*120))),
        "t_cell_01": Def(DT.deci, None, IR(90+(offset*120))),
        "t_cell_02": Def(DT.deci, None, IR(91+(offset*120))),
        "t_cell_03": Def(DT.deci, None, IR(92+(offset*120))),
        "t_cell_04": Def(DT.deci, None, IR(93+(offset*120))),
        "t_cell_05": Def(DT.deci, None, IR(94+(offset*120))),
        "t_cell_06": Def(DT.deci, None, IR(95+(offset*120))),
        "t_cell_07": Def(DT.deci, None, IR(96+(offset*120))),
        "t_cell_08": Def(DT.deci, None, IR(97+(offset*120))),
        "t_cell_09": Def(DT.deci, None, IR(98+(offset*120))),
        "t_cell_10": Def(DT.deci, None, IR(99+(offset*120))),
        "t_cell_11": Def(DT.deci, None, IR(100+(offset*120))),
        "t_cell_12": Def(DT.deci, None, IR(101+(offset*120))),
        "t_cell_13": Def(DT.deci, None, IR(102+(offset*120))),
        "t_cell_14": Def(DT.deci, None, IR(103+(offset*120))),
        "t_cell_15": Def(DT.deci, None, IR(104+(offset*120))),
        "t_cell_16": Def(DT.deci, None, IR(105+(offset*120))),
        "t_cell_17": Def(DT.deci, None, IR(106+(offset*120))),
        "t_cell_18": Def(DT.deci, None, IR(107+(offset*120))),
        "t_cell_19": Def(DT.deci, None, IR(108+(offset*120))),
        "t_cell_20": Def(DT.deci, None, IR(109+(offset*120))),
        "t_cell_21": Def(DT.deci, None, IR(110+(offset*120))),
        "t_cell_22": Def(DT.deci, None, IR(111+(offset*120))),
        "t_cell_23": Def(DT.deci, None, IR(112+(offset*120))),
        "t_cell_24": Def(DT.deci, None, IR(113+(offset*120))),
        "serial_number": Def(
            DT.string, None, IR(114+(offset*120)), IR(115+(offset*120)), IR(116+(offset*120)), IR(117+(offset*120)), IR(118+(offset*120))
        ),
        "BCU": self.offset,
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
