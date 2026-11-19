#include <array>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>

using Scores = std::array<double, 6>;

double model1(const Scores& x, const Scores& weights) {
    double product = 1.0;
    for (std::size_t i = 0; i < x.size(); ++i) {
        product *= std::pow(x[i], weights[i]);
    }
    return product;
}

double model2(const Scores& x, const Scores& weights, double rho) {
    double sum = 0.0;
    for (std::size_t i = 0; i < x.size(); ++i) {
        sum += weights[i] * std::pow(x[i], -rho);
    }
    return std::pow(sum, -1.0 / rho);
}

int main() {
    constexpr Scores weights = {0.15, 0.20, 0.15, 0.15, 0.20, 0.15};
    struct Case {
        int system;
        Scores x;
        double rho;
    };
    constexpr std::array<Case, 2> cases = {{
        {1, {8.6, 9.2, 9.0, 8.9, 9.0, 8.9}, 0.01},
        {2, {8.7, 9.0, 9.2, 9.0, 8.9, 9.1}, 0.15}
    }};

    std::cout << "3.2 (2) Reliability attribute scores\n"
              << "Model 1: y_1 = product(x_i^w_i)\n"
              << "Model 2: y_2 = [sum(w_i*x_i^(-rho_y))]^(-1/rho_y)\n\n"
              << "System       rho_y          y_1          y_2\n"
              << std::fixed << std::setprecision(6);

    for (const Case& data : cases) {
        std::cout << std::setw(6) << data.system
                  << std::setw(12) << data.rho
                  << std::setw(13) << model1(data.x, weights)
                  << std::setw(13) << model2(data.x, weights, data.rho) << '\n';
    }
    std::cout << '\n' << std::flush;
    std::system("pause");
}
