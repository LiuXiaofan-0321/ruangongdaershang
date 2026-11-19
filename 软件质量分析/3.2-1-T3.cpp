#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>

struct Case {
    int system;
    int row;
    std::array<double, 9> y;
    double epsilon;
    double rho;
};

int main() {
    constexpr std::array<double, 5> criticalWeights = {0.25, 0.20, 0.30, 0.15, 0.10};
    constexpr std::array<double, 4> noncriticalWeights = {0.30, 0.30, 0.25, 0.15};
    constexpr double alpha = 0.65;
    constexpr double beta = 0.35;

    constexpr std::array<Case, 4> cases = {{
        {1, 1, {8.1, 7.8, 7.9, 10.0, 9.3, 8.9, 8.9, 9.0, 8.4}, 0.10, 0.05},
        {1, 2, {8.3, 5.6, 7.8,  9.1, 9.2, 7.8, 8.8, 7.8, 8.2}, 0.12, 0.10},
        {2, 1, {7.8, 9.2, 9.0,  9.1, 8.3, 8.2, 6.5, 9.1, 8.9}, 0.10, 0.06},
        {2, 2, {7.9, 9.0, 9.2,  9.0, 6.8, 7.8, 7.6, 7.7, 7.8}, 0.15, 0.16}
    }};

    std::cout << "3.2 (1) Software trustworthiness with T3\n"
              << "A = (min(y1,...,y5)/10)^epsilon * product(y_i^alpha_i)\n"
              << "B = product(y_i^beta_i) for i = 6,...,9\n"
              << "T3 = [0.65*A^(-rho) + 0.35*B^(-rho)]^(-1/rho)\n\n"
              << "System  Row      epsilon       rho            A            B           T3\n"
              << std::fixed << std::setprecision(6);

    for (const Case& data : cases) {
        const auto criticalEnd = data.y.begin() + criticalWeights.size();
        const double minimum = *std::min_element(data.y.begin(), criticalEnd);
        double criticalPart = std::pow(minimum / 10.0, data.epsilon);
        for (std::size_t i = 0; i < criticalWeights.size(); ++i) {
            criticalPart *= std::pow(data.y[i], criticalWeights[i]);
        }

        double noncriticalPart = 1.0;
        for (std::size_t i = 0; i < noncriticalWeights.size(); ++i) {
            noncriticalPart *= std::pow(criticalEnd[i], noncriticalWeights[i]);
        }

        const double t3 = std::pow(alpha * std::pow(criticalPart, -data.rho)
                                 + beta * std::pow(noncriticalPart, -data.rho),
                                 -1.0 / data.rho);
        std::cout << std::setw(6) << data.system
                  << std::setw(5) << data.row
                  << std::setw(13) << data.epsilon
                  << std::setw(10) << data.rho
                  << std::setw(13) << criticalPart
                  << std::setw(13) << noncriticalPart
                  << std::setw(13) << t3 << '\n';
    }
    std::cout << '\n' << std::flush;
    std::system("pause");
}
