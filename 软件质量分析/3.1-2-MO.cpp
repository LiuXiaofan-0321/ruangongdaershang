#include <array>
#include <cmath>
#include <cstdlib>
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

void runMo(double elapsed) {
    constexpr std::array<double, 28> intervals = {
        9, 12, 11, 4, 7, 2, 5, 1, 7, 12, 6, 11, 9, 7,
        13, 3, 6, 11, 3, 6, 13, 21, 10, 7, 7, 12, 19, 15
    };
    std::array<double, intervals.size()> failureTimes{};
    std::partial_sum(intervals.begin(), intervals.end(), failureTimes.begin());
    const double count = failureTimes.size();
    const double lastTime = failureTimes.back();

    // 令 q = beta1 * t_n，消去 beta0 后求 beta1 的极大似然估计。
    const auto score = [&](double q) {
        double inverseSum = 0.0;
        for (double time : failureTimes) {
            inverseSum += 1.0 / (1.0 + q * (time / lastTime));
        }
        return inverseSum - count * q / ((1.0 + q) * std::log1p(q));
    };

    const double q = solvePositiveToNegative(score, 1e-6, 1.0);
    const double beta0 = count / std::log1p(q);
    const double beta1 = q / lastTime;
    const double lambda0 = beta0 * beta1;
    const double theta = 1.0 / beta0;

    // x 是第 28 次失效之后经过的时间。
    const double logRatio = std::log1p(beta1 * elapsed / (1.0 + q));
    const double meanIncrement = beta0 * logRatio;
    const double mean = beta0 * std::log1p(q) + meanIncrement;
    const double intensity = lambda0 / (1.0 + q + beta1 * elapsed);
    const double reliability = std::exp(-meanIncrement);
    const double unreliability = -std::expm1(-meanIncrement);
    const double density = intensity * reliability;

    std::cout << "3.1 (2) Musa-Okumoto log-Poisson NHPP model\n"
              << "n = " << failureTimes.size() << ", t_n = " << lastTime << " s\n"
              << "beta0 = " << beta0 << ", beta1 = " << beta1 << '\n'
              << "lambda0 = " << lambda0 << " /s, theta = " << theta << '\n'
              << "t = t_n + x, x >= 0\n"
              << "lambda(t) = beta0*beta1 / (1 + beta1*t)\n"
              << "mu(t) = beta0*ln(1 + beta1*t)\n"
              << "Mean number of additional failures in x: mu(t_n+x) - mu(t_n)\n"
              << "R_29(x) = [(1 + beta1*t_n)/(1 + beta1*(t_n+x))]^beta0\n"
              << "F_29(x) = 1 - R_29(x)\n"
              << "f_29(x) = lambda(t_n+x)*R_29(x)\n";

    if (beta0 > 1) {
        const double mttf = (1.0 + q) / (beta1 * (beta0 - 1.0));
        std::cout << "MTTF_29 = (1 + beta1*t_n)/(beta1*(beta0-1)) = "
                  << mttf << " s\n";
    } else {
        std::cout << "MTTF_29 is infinite (beta0 <= 1).\n";
    }

    std::cout << "At x = " << elapsed << " s: lambda = " << intensity
              << " /s, mu = " << mean << ", delta_mu = " << meanIncrement << '\n'
              << "R = " << reliability << ", F = " << unreliability
              << ", f = " << density << " /s\n";
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
        runMo(elapsed);
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
    std::cout << '\n' << std::flush;
    std::system("pause");
}
