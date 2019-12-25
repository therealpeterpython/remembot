HOURS = 24
MINUTES = 60


def get_divisors(x):
    return [i for i in range(1, x + 1) if not divmod(x, i)[1]]


h_divisors = get_divisors(HOURS)
m_divisors = get_divisors(MINUTES)

commons = [i for i in h_divisors if i in m_divisors and i > 2]

h_sizes = [HOURS//i for i in commons]
m_sizes = [MINUTES//i for i in commons]

commons2 = list()
for i in range(len(commons)):
    h_sizes_divisors = get_divisors(h_sizes[i])
    m_sizes_divisors = get_divisors(m_sizes[i])
    com = [i for i in h_sizes_divisors if i in m_sizes_divisors if i>1]
    print("Erste Höhe: ", commons[i])
    print("Zweite Höhen: ", com,"\n")
    commons2.append(com)


#print(h_divisors)
#print(m_divisors)
#print(commons)
#print(h_sizes)
#print(m_sizes)
#print(commons2)

print(list(zip(commons,commons2)))

