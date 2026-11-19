#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>

constexpr std::size_t dimension = 5;
constexpr int maxIterations = 100000;
using Weights = std::array<double, dimension>;
using Matrix = std::array<Weights, dimension>;

Weights normalize(Weights weights) {
    const double sum = std::accumulate(weights.begin(), weights.end(), 0.0);
    for (double& weight : weights) {
        weight /= sum;
    }
    return weights;
}

Weights multiply(const Matrix& a, const Weights& weights) {
    Weights result{};
    for (std::size_t i = 0; i < dimension; ++i) {
        result[i] = std::inner_product(a[i].begin(), a[i].end(), weights.begin(), 0.0);
    }
    return result;
}

// EV：幂迭代求主右特征向量，并将向量归一化。
Weights eigenvectorMethod(const Matrix& a) {
    Weights weights{};
    weights.fill(1.0 / dimension);
    for (int iteration = 0; iteration < maxIterations; ++iteration) {
        const Weights next = normalize(multiply(a, weights));
        double difference = 0.0;
        for (std::size_t i = 0; i < dimension; ++i) {
            difference = std::max(difference, std::abs(next[i] - weights[i]));
        }
        if (difference < 1e-13) {
            return next;
        }
        weights = next;
    }
    throw std::runtime_error("EV iteration did not converge.");
}

// LLSM：对判断矩阵各行的几何平均数归一化。
Weights logarithmicLeastSquares(const Matrix& a) {
    Weights roots{};
    for (std::size_t i = 0; i < dimension; ++i) {
        const double product = std::accumulate(a[i].begin(), a[i].end(), 1.0,
            [](double left, double right) { return left * right; });
        roots[i] = std::pow(product, 1.0 / dimension);
    }
    return normalize(roots);
}

// CSM：按第四章 PDF 第 95—97 页例程，更新绝对偏差最大的分量后归一化。
Weights chiSquareMethod(const Matrix& a) {
    constexpr double tolerance = 1e-10;
    Weights weights{};
    weights.fill(1.0 / dimension);

    for (int iteration = 0; iteration < maxIterations; ++iteration) {
        std::size_t selected = 0;
        double largest = 0.0;
        for (std::size_t i = 0; i < dimension; ++i) {
            double deviation = 0.0;
            for (std::size_t j = 0; j < dimension; ++j) {
                deviation += (1.0 + a[j][i] * a[j][i]) * (weights[i] / weights[j])
                           - (1.0 + a[i][j] * a[i][j]) * (weights[j] / weights[i]);
            }
            if (std::abs(deviation) > largest) {
                largest = std::abs(deviation);
                selected = i;
            }
        }
        if (largest <= tolerance) {
            return weights;
        }

        double numerator = 0.0;
        double denominator = 0.0;
        for (std::size_t j = 0; j < dimension; ++j) {
            if (j == selected) {
                continue;
            }
            numerator += (1.0 + a[selected][j] * a[selected][j]) * (weights[j] / weights[selected]);
            denominator += (1.0 + a[j][selected] * a[j][selected]) * (weights[selected] / weights[j]);
        }
        weights[selected] *= std::sqrt(numerator / denominator);
        weights = normalize(weights);
    }
    throw std::runtime_error("CSM iteration did not converge.");
}

double totalDeviation(const Matrix& a, const Weights& weights) {
    double td = 0.0;
    for (std::size_t i = 0; i < dimension; ++i) {
        for (std::size_t j = 0; j < dimension; ++j) {
            td += std::abs(a[i][j] - weights[i] / weights[j]);
        }
    }
    return td;
}

void printWeights(const Weights& weights) {
    std::cout << weights.front();
    for (std::size_t i = 1; i < weights.size(); ++i) {
        std::cout << ", " << weights[i];
    }
}

int main() {
    constexpr Matrix a = {{
        {1.0, 0.25, 2.0, 2.0,  0.5},
        {4.0, 1.0,  2.0, 0.25, 0.5},
        {0.5, 0.5,  1.0, 0.25, 2.0},
        {0.5, 4.0,  4.0, 1.0,  2.0},
        {2.0, 2.0,  0.5, 0.5,  1.0}
    }};

    try {
        const Weights ev = eigenvectorMethod(a);
        const Weights llsm = logarithmicLeastSquares(a);
        const Weights csm = chiSquareMethod(a);
        const Weights weightedEv = multiply(a, ev);
        const double lambdaMax = std::accumulate(weightedEv.begin(), weightedEv.end(), 0.0);

        struct Result {
            const char* name;
            Weights weights;
            double td;
        };
        const std::array<Result, 3> results = {{
            {"EV", ev, totalDeviation(a, ev)},
            {"LLSM", llsm, totalDeviation(a, llsm)},
            {"CSM", csm, totalDeviation(a, csm)}
        }};
        const auto best = std::min_element(results.begin(), results.end(),
            [](const Result& left, const Result& right) { return left.td < right.td; });

        std::cout << std::fixed << std::setprecision(6)
                  << "3.3 Flight-control software attribute weights\n"
                  << "Order: timeliness, reliability, survivability, maintainability, functionality\n"
                  << "EV principal eigenvalue = " << lambdaMax << "\n"
                  << "CSM: lecture iteration, Chapter 4, pp. 95-97\n"
                  << "Strength criterion: TD = sum_ij |a_ij - w_i/w_j|\n\n";
        for (const Result& result : results) {
            std::cout << std::left << std::setw(5) << result.name << std::right << '(';
            printWeights(result.weights);
            std::cout << ")  TD = " << result.td << '\n';
        }
        std::cout << "\nBest by minimum TD: " << best->name << "\nW^CSM=={";
        printWeights(csm);
        std::cout << "}\n\n" << std::flush;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
    std::system("pause");
}
