#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>

template <typename Function>
double solvePositiveToNegative(Function equation, double lower, double upper) {
    if (equation(lower) <= 0 || equation(upper) > 0) {
        throw std::runtime_error("The estimation equation has no root in the search interval.");
    }

    for (int step = 0; step < 80; ++step) {
        const double middle = lower + (upper - lower) / 2;
        if (equation(middle) > 0) {
            lower = middle;
        } else {
            upper = middle;
        }
    }
    return lower + (upper - lower) / 2;
}

void runJm(double elapsed) {
    constexpr std::array<double, 12> intervals = {
        10, 12, 9, 14, 18, 20, 14, 16, 30, 23, 14, 25
    };
    const double count = intervals.size();
    const double total = std::accumulate(intervals.begin(), intervals.end(), 0.0);
    double weightedTotal = 0.0;
    for (std::size_t i = 0; i < intervals.size(); ++i) {
        weightedTotal += i * intervals[i];
    }

    // 极大似然方程中的 i 从 0 起算，对应课件中的 i - 1。
    const auto score = [&](double initialFaults) {
        double inverseSum = 0.0;
        for (std::size_t i = 0; i < intervals.size(); ++i) {
            inverseSum += 1.0 / (initialFaults - i);
        }
        return inverseSum - count / (initialFaults - weightedTotal / total);
    };

    const double initialFaults = solvePositiveToNegative(score, count, 1000.0);
    const double k = count / (initialFaults * total - weightedTotal);
    const double lambda = k * (initialFaults - count);
    const double reliability = std::exp(-lambda * elapsed);
    const double unreliability = -std::expm1(-lambda * elapsed);
    const double density = lambda * reliability;

    std::cout << "3.1 (1) Jelinski-Moranda model\n"
              << "n = " << intervals.size() << ", sum(x_i) = " << total
              << ", sum((i-1)*x_i) = " << weightedTotal << '\n'
              << "N = " << initialFaults << ", k = " << k << ", lambda = " << lambda << '\n'
              << "R_13(x) = exp(-lambda*x)\n"
              << "F_13(x) = 1 - R_13(x)\n"
              << "f_13(x) = lambda*R_13(x)\n"
              << "MTTF_13 = " << 1.0 / lambda << " s\n"
              << "At x = " << elapsed << " s: R = " << reliability
              << ", F = " << unreliability << ", f = " << density << " /s\n";
}

int main(int argc, char* argv[]) {
    try {
        double elapsed = 0.0;
        if (argc == 2) {
            std::size_t used = 0;
            elapsed = std::stod(argv[1], &used);
            if (argv[1][used] != '\0' || !std::isfinite(elapsed) || elapsed < 0) {
                throw std::invalid_argument("x must be a finite, nonnegative time in seconds.");
            }
        } else if (argc > 2) {
            throw std::invalid_argument("Pass at most one time x in seconds.");
        }

        std::cout << std::fixed << std::setprecision(10);
        runJm(elapsed);
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
