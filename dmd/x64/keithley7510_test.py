import pyvisa as visa
import time
import numpy as np

rm = visa.ResourceManager()
address = "USB0::0x05E6::0x7510::04635910::0::INSTR"

multi = rm.open_resource(address)

multi.write('VOLT:AZER OFF')
multi.write('VOLT:NPLC 0.2')
multi.write('VOLT:RANG:AUTO OFF')
multi.write('SENS:VOLT:RANG 10')

multi.write('FUNC "VOLT"')
multi.write('AZER:ONCE')
time.sleep(1.0)
N=1000
t_arr = np.full(N, 0.0)
for i in range(N):
    start = time.time()
    idn = multi.query("READ?")
    print(idn)
    end = time.time()

    t_arr[i] = end-start

#print(idn)
print(f'Mean: {np.mean(t_arr)}')
print(f'Max: {np.max(t_arr)}')