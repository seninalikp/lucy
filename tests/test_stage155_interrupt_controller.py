r"""
tests/test_stage155_interrupt_controller.py
Stage 155 Test Suite: Interrupt Service Routine (ISR) & PIC/APIC Controller
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.interrupt_controller import (
    CREATOR,
    ERA,
    EXC_DIVIDE_BY_ZERO,
    EXC_PAGE_FAULT,
    IDT_TOTAL_VECTORS,
    INT_SYSCALL_GATEWAY,
    IRQ_KEYBOARD,
    IRQ_TIMER,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    GateType,
    IDTDescriptor,
    InterruptFrame,
    PIC8259Simulator,
    SovereignInterruptController,
    get_interrupt_controller,
)


class TestStage155InterruptController(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = SovereignInterruptController()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 155)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Interrupt Service Routine (ISR) & PIC/APIC Controller",
        )
        self.assertEqual(IDT_TOTAL_VECTORS, 256)

    def test_02_idt_initialization(self) -> None:
        self.assertEqual(len(self.controller.idt), 256)
        # Exception 0 (Divide-by-zero) must be present
        de = self.controller.idt[EXC_DIVIDE_BY_ZERO]
        self.assertTrue(de.present)
        self.assertIn("Divide-by-Zero", de.name)

        # Vector 14 (Page Fault) must be present
        pf = self.controller.idt[EXC_PAGE_FAULT]
        self.assertTrue(pf.present)
        self.assertIn("Page Fault", pf.name)

    def test_03_pic_mask_and_unmask(self) -> None:
        pic = PIC8259Simulator()
        self.assertFalse(pic.is_irq_masked(0))

        # Mask IRQ 0 (timer)
        pic.mask_irq(0)
        self.assertTrue(pic.is_irq_masked(0))
        self.assertEqual(pic.master_imr & 1, 1)

        # Unmask IRQ 0
        pic.unmask_irq(0)
        self.assertFalse(pic.is_irq_masked(0))

        # Test slave PIC (IRQ 8)
        pic.mask_irq(8)
        self.assertTrue(pic.is_irq_masked(8))
        self.assertEqual(pic.slave_imr & 1, 1)

    def test_04_hardware_irq_blocking_when_masked(self) -> None:
        # Mask IRQ 0 (Vector 32)
        self.controller.pic.mask_irq(0)
        ok, reason = self.controller.trigger_interrupt(IRQ_TIMER)
        self.assertFalse(ok)
        self.assertIn("masked", reason)

        # Unmask IRQ 0
        self.controller.pic.unmask_irq(0)
        ok2, _ = self.controller.trigger_interrupt(IRQ_TIMER)
        self.assertTrue(ok2)

    def test_05_interrupt_flag_disable_enable(self) -> None:
        self.assertTrue(self.controller.interrupt_flag)

        # Clear Interrupt Flag (CLI)
        self.controller.disable_interrupts()
        self.assertFalse(self.controller.interrupt_flag)

        # Hardware IRQ should be blocked
        ok, reason = self.controller.trigger_interrupt(IRQ_KEYBOARD)
        self.assertFalse(ok)
        self.assertIn("disabled", reason)

        # Set Interrupt Flag (STI)
        self.controller.enable_interrupts()
        ok2, _ = self.controller.trigger_interrupt(IRQ_KEYBOARD)
        self.assertTrue(ok2)

    def test_06_custom_isr_registration(self) -> None:
        handled_frames = []

        def my_custom_handler(frame: InterruptFrame):
            handled_frames.append(frame)
            return "HANDLER_EXECUTED_OK"

        ok_reg = self.controller.register_isr(
            vector=0x50,
            handler=my_custom_handler,
            name="Custom High Priority Handler",
            gate_type=GateType.INTERRUPT_GATE,
        )
        self.assertTrue(ok_reg)

        ok_trig, res = self.controller.trigger_interrupt(0x50, error_code=None)
        self.assertTrue(ok_trig)
        self.assertEqual(res, "HANDLER_EXECUTED_OK")
        self.assertEqual(len(handled_frames), 1)
        self.assertEqual(handled_frames[0].vector, 0x50)

    def test_07_syscall_gateway_invocation(self) -> None:
        syscall_called = []

        def syscall_isr(frame: InterruptFrame):
            syscall_called.append(frame.rip)
            return 0  # Syscall return status 0

        self.controller.register_isr(INT_SYSCALL_GATEWAY, syscall_isr)
        ok, res = self.controller.trigger_interrupt(INT_SYSCALL_GATEWAY, context_regs={"rip": 0x401050})
        self.assertTrue(ok)
        self.assertEqual(res, 0)
        self.assertEqual(syscall_called, [0x401050])

    def test_08_error_code_delivery(self) -> None:
        captured_error = []

        def pf_handler(frame: InterruptFrame):
            captured_error.append(frame.error_code)
            return "PF_RESOLVED"

        self.controller.register_isr(EXC_PAGE_FAULT, pf_handler)
        ok, res = self.controller.trigger_interrupt(EXC_PAGE_FAULT, error_code=0x07)
        self.assertTrue(ok)
        self.assertEqual(res, "PF_RESOLVED")
        self.assertEqual(captured_error, [0x07])

    def test_09_unregistered_vector_rejection(self) -> None:
        # Vector 0xFE unhandled initially
        self.controller.unregister_isr(0xFE)
        ok, reason = self.controller.trigger_interrupt(0xFE)
        self.assertFalse(ok)
        self.assertIn("not present", reason)

    def test_10_ascii_status_presentation(self) -> None:
        self.controller.trigger_interrupt(IRQ_TIMER)
        status = self.controller.format_ascii_status()
        self.assertIn("LUCY STAGE 155", status)
        self.assertIn("Senin", status)
        self.assertIn("Divide-by-Zero", status)
        self.assertIn("Syscall Gateway", status)


if __name__ == "__main__":
    unittest.main()
