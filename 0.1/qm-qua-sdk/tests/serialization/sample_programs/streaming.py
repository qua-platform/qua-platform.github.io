from qm.qua import *
import numpy as np

i32 = np.int32

with program() as prog:
    x = declare(int)
    stream = declare_stream()
    save(x, stream)
    measure("fdsa", "fds", stream)

    save(x, "str")

    stream2 = declare_stream()
    measure("fdsa", "fds", stream2)

    y = declare(fixed)
    stream3 = declare_stream()
    save(y, stream)
    save(y, stream3)

    with stream_processing():
        stream.save("final_tag")
        stream.boolean_to_int().save("bool_to_int")
        stream.timestamps().save("final_tag_timestamps")
        stream.with_timestamps().save("final_tag_with_timestamps")
        stream.buffer(1).buffer(1, 2).flatten().buffer_and_skip(5, 1).save("buffer")
        stream.average().map(FUNCTIONS.average()).save("avg")
        stream.average().map(FUNCTIONS.average(0)).save("avg0")
        stream.average().map(FUNCTIONS.average(1)).save("avg1")
        stream.dot_product([1, 2, 3]).convolution([4, 5, 6]).save("conv_dot")
        stream.multiply_by(5).multiply_by([1, 2]).multiply(3).save("mult")
        stream.tuple_multiply().tuple_convolution(mode="full").save("tuple1")
        stream.tuple_dot_product().save("tuple2")
        stream.fft().histogram(bins(0, 1, 2)).save("fft_hist")
        stream.subtract(5).divide(stream).add(3).multiply(stream).save("arithmetic")
        stream.skip_last(10).skip(10).boolean_to_int().take(10).save("skip_take")
        stream.auto_reshape().zip(stream).save_all("auto_reshape")
        stream2.save_all('save_all')


with program() as stream_processing_prog_with_numpy:
    x = declare(int)
    stream = declare_stream()
    save(x, stream)
    measure("fdsa", "fds", stream)

    save(x, "str")

    with stream_processing():
        stream.save("final_tag")
        stream.timestamps().save("final_tag_timestamps")
        stream.with_timestamps().save("final_tag_with_timestamps")
        stream.buffer(i32(1)).buffer(i32(1), i32(2)).flatten().buffer_and_skip(i32(5), i32(1)).save("buffer")
        stream.average().map(FUNCTIONS.average()).save("avg")
        stream.dot_product(np.array([1, 2, 3], dtype=i32)).convolution(np.array([4, 5, 6], dtype=i32)).save("conv_dot")
        stream.multiply_by(i32(5)).multiply_by(np.array([1, 2], dtype=i32)).multiply(i32(3)).save("mult")
        stream.tuple_multiply().tuple_convolution(mode="full").save("tuple1")
        stream.tuple_dot_product().save("tuple2")
        stream.fft().histogram(bins(i32(0), i32(1), i32(2))).save("fft_hist")
        stream.subtract(i32(5)).divide(stream).add(i32(3)).multiply(stream).save("arithmetic")
        stream.skip_last(i32(10)).skip(i32(10)).boolean_to_int().take(i32(10)).save("skip_take")
        stream.auto_reshape().zip(stream).save_all("auto_reshape")

with program() as adc_trace:
    stream2 = declare_stream(adc_trace=True)
    stream3 = declare_stream()
    stream4 = declare_stream(adc_trace=True)
    stream5 = declare_stream()
    measure("op1", "el1", stream2)
    measure("op1" * amp(0.1), "el1", stream3)
    measure("op1", "el1", stream4)
    measure("op1" * amp(0.1), "el1", stream5)
    measure('op2', 'el2', "A")
    measure('op2' * amp(0.1), 'el2', "B")

    with stream_processing():
        stream2.input1().save_all('adc_trace2')
        stream5.input1().save_all('adc_trace5')

with program() as legacy_save:
    var = declare(int)
    stream = declare_stream()
    save(var, "yo")

with program() as wrong_order:
    stream1 = declare_stream()
    stream2 = declare_stream()
    var1 = declare(int)
    var2 = declare(int)
    var3 = declare(int)

    save(var2, stream2)
    save(var3, "yo3")
    save(var1, stream1)

    with stream_processing():
        stream1.save('yo1')
        stream2.save('yo2')
