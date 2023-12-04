
x = [1,0,0 , 1,1,1 , 0,1,1]


charge_discharge_bits = x[:, 0]
percentage_bits = x[:, 1:].reshape((3, 2))

print(charge_discharge_bits)
print(percentage_bits)