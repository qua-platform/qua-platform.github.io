from qm.octave._calibration_config import offset_amp
from qm.qua import (
    assign,
    for_,
    reset_phase,
    align,
    play,
    measure,
    dual_demod,
    if_,
    save,
    amp,
    update_correction,
    else_,
    while_,
    program,
    declare,
    fixed,
    declare_stream,
    wait,
    stream_processing,
)


def _generate_program(calibration_parameters):
    n_average = calibration_parameters["average_iterations"]
    iterations = calibration_parameters["iterations"]
    keep_on = calibration_parameters["keep_on"]
    initial_step_size = 2**-5

    def read_all_power():
        assign(avg_signal_power, 0)
        assign(avg_lo_power, 0)
        assign(avg_image_power, 0)

        with for_(index, 0, index < n_average, index + 1):
            reset_phase("IQmixer")
            reset_phase("signal_analyzer")
            reset_phase("lo_analyzer")
            reset_phase("image_analyzer")
            align(
                "IQmixer",
                "signal_analyzer",
                "lo_analyzer",
                "image_analyzer",
                "I_offset",
                "Q_offset",
            )

            play("calibration", "IQmixer")
            measure(
                "Analyze",
                "signal_analyzer",
                None,
                dual_demod.full("integW_cos", "out1", "integW_sin", "out2", I1),
                dual_demod.full("integW_cos", "out2", "integW_minus_sin", "out1", Q1),
            )
            measure(
                "Analyze",
                "lo_analyzer",
                None,
                dual_demod.full("integW_cos", "out1", "integW_sin", "out2", I2),
                dual_demod.full("integW_cos", "out2", "integW_minus_sin", "out1", Q2),
            )
            measure(
                "Analyze",
                "image_analyzer",
                None,
                dual_demod.full("integW_cos", "out1", "integW_sin", "out2", I3),
                dual_demod.full("integW_cos", "out2", "integW_minus_sin", "out1", Q3),
            )
            assign(
                avg_signal_power,
                avg_signal_power + (I1 * I1 + Q1 * Q1),
            )
            with if_(avg_signal_power < -1.0):
                save(avg_signal_power, "error")
            assign(
                avg_lo_power,
                avg_lo_power + (I2 * I2 + Q2 * Q2),
            )
            with if_(avg_lo_power < -1.0):
                save(avg_lo_power, "error")
            assign(
                avg_image_power,
                avg_image_power + (I3 * I3 + Q3 * Q3),
            )
            with if_(avg_image_power < -1.0):
                save(avg_image_power, "error")

        # assign(avg_signal_power, avg_signal_power * float(1 / n_average))
        # assign(avg_lo_power, avg_lo_power * float(1 / n_average))
        # assign(avg_image_power, avg_image_power * float(1 / n_average))

    def read_lo_and_image_power():
        assign(avg_lo_power, 0)
        assign(avg_image_power, 0)
        with for_(index, 0, index < n_average, index + 1):
            reset_phase("IQmixer")
            reset_phase("lo_analyzer")
            reset_phase("image_analyzer")
            align("IQmixer", "lo_analyzer", "image_analyzer", "I_offset", "Q_offset")
            play("calibration", "IQmixer")
            measure(
                "Analyze",
                "lo_analyzer",
                None,
                dual_demod.full("integW_cos", "out1", "integW_sin", "out2", I2),
                dual_demod.full("integW_cos", "out2", "integW_minus_sin", "out1", Q2),
            )
            measure(
                "Analyze",
                "image_analyzer",
                None,
                dual_demod.full("integW_cos", "out1", "integW_sin", "out2", I3),
                dual_demod.full("integW_cos", "out2", "integW_minus_sin", "out1", Q3),
            )
            assign(
                avg_lo_power,
                avg_lo_power + (I2 * I2 + Q2 * Q2),
            )
            with if_(avg_lo_power < -1.0):
                save(avg_lo_power, "error")
            assign(
                avg_image_power,
                avg_image_power + (I3 * I3 + Q3 * Q3),
            )
            with if_(avg_image_power < -1.0):
                save(avg_image_power, "error")

    def update_correction_g_phi():
        assign(s_mat, curr_phase)
        assign(s2, s_mat * s_mat)
        assign(c_mat, 1 + 1.5 * s2 - 3.125 * (s2 * s2))
        assign(g_mat_plus, 1 + curr_gain + curr_gain * curr_gain)
        assign(g_mat_minus, 1 - curr_gain + curr_gain * curr_gain)
        assign(c00, g_mat_minus * c_mat)
        assign(c01, g_mat_plus * s_mat)
        assign(c10, g_mat_minus * s_mat)
        assign(c11, g_mat_plus * c_mat)
        update_correction("IQmixer", c00, c01, c10, c11)

    def search_1_direction(which):
        with if_(lo_cont):
            # LO
            if which == "i_g":
                assign(curr_i0, curr_i0 + step_size_lo)
                play("DC_offset" * amp(step_size_lo), "I_offset")
            else:
                assign(curr_q0, curr_q0 + step_size_lo)
                play("DC_offset" * amp(step_size_lo), "Q_offset")
        with if_(image_cont):
            # image
            if which == "i_g":
                assign(curr_gain, curr_gain + step_size_image)
            else:
                assign(curr_phase, curr_phase + step_size_image)
            update_correction_g_phi()

        read_lo_and_image_power()
        with if_(lo_cont):
            # LO
            with if_(avg_lo_power < best_lo_power):  # Current direction is good
                assign(curr_step_lo, step_size_lo)
            with else_():  # Need to check other direction
                assign(curr_step_lo, -step_size_lo)
                if which == "i_g":
                    assign(curr_i0, curr_i0 + curr_step_lo)
                    play("DC_offset" * amp(curr_step_lo), "I_offset")
                else:
                    assign(curr_q0, curr_q0 + curr_step_lo)
                    play("DC_offset" * amp(curr_step_lo), "Q_offset")
                assign(avg_lo_power, best_lo_power)
        with if_(image_cont):
            # image
            with if_(avg_image_power < best_image_power):  # Current direction is good
                assign(curr_step_image, step_size_image)
            with else_():  # Need to check other direction
                assign(curr_step_image, -step_size_image)
                if which == "i_g":
                    assign(curr_gain, curr_gain + curr_step_image)
                else:
                    assign(curr_phase, curr_phase + curr_step_image)
                assign(avg_image_power, best_image_power)

        assign(move_lo_cont, lo_cont)
        assign(move_image_cont, image_cont)
        with while_((move_lo_cont | move_image_cont)):
            with if_(move_lo_cont):
                assign(best_lo_power, avg_lo_power)
                save(best_lo_power, lo_stream)
                if which == "i_g":
                    save(curr_i0, "i_track")
                    assign(curr_i0, curr_i0 + curr_step_lo)
                    play("DC_offset" * amp(curr_step_lo), "I_offset")
                else:
                    save(curr_q0, "q_track")
                    assign(curr_q0, curr_q0 + curr_step_lo)
                    play("DC_offset" * amp(curr_step_lo), "Q_offset")
            with if_(move_image_cont):
                assign(best_image_power, avg_image_power)
                save(best_image_power, image_stream)
                if which == "i_g":
                    save(curr_gain, "g_track")
                    assign(curr_gain, curr_gain + curr_step_image)
                else:
                    save(curr_phase, "phi_track")
                    assign(curr_phase, curr_phase + curr_step_image)
                update_correction_g_phi()
            assign(counter, counter + 1)
            read_lo_and_image_power()
            with if_(move_lo_cont):
                assign(move_lo_cont, avg_lo_power < best_lo_power)
            with if_(move_image_cont):
                assign(move_image_cont, avg_image_power < best_image_power)

        with if_(lo_cont):
            if which == "i_g":
                assign(curr_i0, curr_i0 - curr_step_lo)
                play("DC_offset" * amp(-curr_step_lo), "I_offset")
            else:
                assign(curr_q0, curr_q0 - curr_step_lo)
                play("DC_offset" * amp(-curr_step_lo), "Q_offset")
        with if_(image_cont):
            if which == "i_g":
                assign(curr_gain, curr_gain - curr_step_image)
            else:
                assign(curr_phase, curr_phase - curr_step_image)
            update_correction_g_phi()

    with program() as OPMix_minimize_line_search:
        index = declare(int)

        # variables for getting IQ data
        Q1 = declare(fixed)
        Q2 = declare(fixed)
        Q3 = declare(fixed)
        I1 = declare(fixed)
        I2 = declare(fixed)
        I3 = declare(fixed)

        # variables for current power
        avg_signal_power = declare(fixed)
        avg_lo_power = declare(fixed)
        avg_image_power = declare(fixed)

        # streams for power
        signal_stream = declare_stream()
        lo_stream = declare_stream()
        image_stream = declare_stream()

        # variables for LO leakage
        curr_i0 = declare(fixed, value=0)
        curr_q0 = declare(fixed, value=0)
        best_lo_power = declare(fixed, value=0)
        step_size_lo = declare(fixed, value=initial_step_size)
        curr_step_lo = declare(fixed, value=0)
        move_lo_cont = declare(bool, value=True)

        # variables for image leakage
        curr_gain = declare(fixed, value=0)
        curr_phase = declare(fixed, value=0)
        best_image_power = declare(fixed, value=0)
        step_size_image = declare(fixed, value=initial_step_size)
        curr_step_image = declare(fixed, value=0)
        move_image_cont = declare(bool, value=True)

        # variables for correction matrix
        g_mat_plus = declare(fixed)
        g_mat_minus = declare(fixed)
        s2 = declare(fixed)
        c_mat = declare(fixed)
        s_mat = declare(fixed)
        c00 = declare(fixed)
        c01 = declare(fixed)
        c10 = declare(fixed)
        c11 = declare(fixed)

        # iterations
        bool_lo_power_small = declare(bool)
        bool_lo_step_size_small = declare(bool)
        bool_image_power_small = declare(bool)
        bool_image_step_size_small = declare(bool)
        bool_too_many_iterations = declare(bool)
        lo_cont = declare(bool, value=True)
        image_cont = declare(bool, value=True)
        counter = declare(int, value=0)

        read_lo_and_image_power()
        save(curr_i0, "i_track")
        save(curr_q0, "q_track")
        save(avg_lo_power, lo_stream)
        save(curr_gain, "g_track")
        save(curr_phase, "phi_track")
        save(avg_image_power, image_stream)
        assign(best_lo_power, avg_lo_power)
        assign(best_image_power, avg_image_power)
        with while_((lo_cont | image_cont)):
            search_1_direction("i_g")
            search_1_direction("q_p")

            assign(step_size_lo, step_size_lo >> 1)  # Divide step size by 2
            assign(step_size_image, step_size_image >> 1)  # Divide step size by 2

            assign(bool_too_many_iterations, counter >= iterations)

            assign(bool_lo_power_small, avg_lo_power < 2**-27)
            assign(
                bool_lo_step_size_small, step_size_lo < 2**-16
            )  # opx fixed point resolution
            assign(
                lo_cont,
                ~(
                    bool_lo_power_small
                    | bool_lo_step_size_small
                    | bool_too_many_iterations
                ),
            )

            assign(bool_image_power_small, avg_image_power < 2**-27)
            assign(
                bool_image_step_size_small, step_size_image < 2**-16
            )  # opx fixed point resolution
            assign(
                image_cont,
                ~(
                    bool_image_power_small
                    | bool_image_step_size_small
                    | bool_too_many_iterations
                ),
            )

        save(bool_lo_power_small, "bool_lo_power_small")
        save(bool_lo_step_size_small, "bool_lo_step_size_small")
        save(bool_image_power_small, "bool_image_power_small")
        save(bool_image_step_size_small, "bool_image_step_size_small")
        save(bool_too_many_iterations, "bool_too_many_iterations")
        save(counter, "counter")

        read_all_power()
        save(avg_signal_power, signal_stream)
        save(avg_lo_power, lo_stream)
        save(avg_image_power, image_stream)
        save(c00, "c00")
        save(c01, "c01")
        save(c10, "c10")
        save(c11, "c11")

        if keep_on:
            with for_(index, 0, index < 1e6, index + 1):
                play("calibration", "IQmixer")
                wait(10, "I_offset")
                wait(10, "Q_offset")

        with stream_processing():
            lo_stream.save_all("lo")
            image_stream.save_all("image")
            signal_stream.save_all("signal")

    return OPMix_minimize_line_search


def _process_results(
    error,
    i_track,
    q_track,
    c00,
    c01,
    c10,
    c11,
):
    if len(error) > 0:
        raise RuntimeError("Readout pulse too long!")

    final_i = i_track[-1] * offset_amp
    final_q = q_track[-1] * offset_amp

    return [final_i, final_q], [c00[0], c01[0], c10[0], c11[0]]
