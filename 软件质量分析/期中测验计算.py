from math import fsum


def estimate_jm(intervals):
    count = len(intervals)
    total = fsum(intervals)
    weighted_total = fsum(i * interval for i, interval in enumerate(intervals))
    weighted_mean = weighted_total / total

    def equation(initial_faults):
        return fsum(1 / (initial_faults - i) for i in range(count)) - (
            count / (initial_faults - weighted_mean)
        )

    lower, upper = float(count), 1000.0
    if equation(lower) * equation(upper) >= 0:
        raise ValueError('No J-M root bracketed in the search interval.')
    lower_sign = equation(lower) > 0
    for _ in range(70):
        midpoint = (lower + upper) / 2
        if (equation(midpoint) > 0) == lower_sign:
            lower = midpoint
        else:
            upper = midpoint

    initial_faults = (lower + upper) / 2
    k = count / (initial_faults * total - weighted_total)
    rate = k * (initial_faults - count)
    return count, total, weighted_total, initial_faults, k, rate


def run_jm():
    intervals = [10, 12, 9, 14, 18, 20, 14, 16, 30, 23, 14, 25]
    count, total, weighted_total, initial_faults, k, rate = estimate_jm(intervals)
    next_failure = count + 1
    print('3.1(1)  Jelinski-Moranda model')
    print(f'n = {count}, S = {total:g}, B = {weighted_total:g}')
    print(f'N0 = {initial_faults:.8f}, k = {k:.10f}, Z = {rate:.10f}')
    print(f'R_{next_failure}(x) = exp(-{rate:.10f} * x)')
    print(f'F_{next_failure}(x) = 1 - exp(-{rate:.10f} * x)')
    print(f'f_{next_failure}(x) = {rate:.10f} * exp(-{rate:.10f} * x)')
    print(f'MTTF_{next_failure} = {1 / rate:.8f}')


if __name__ == '__main__':
    run_jm()
