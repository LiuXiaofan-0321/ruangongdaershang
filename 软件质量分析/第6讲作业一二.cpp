#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>

using namespace std;

// 作业一：不区分关键和非关键属性的乘积模型。
double modelT(const array<double, 5>& y, const array<double, 5>& weight) {
    double result = 1.0;
    for (size_t i = 0; i < y.size(); ++i) {
        result *= pow(y[i], weight[i]);
    }
    return result;
}

// 作业二：前 4 项为关键属性，后 3 项为非关键属性。
double modelT3(const array<double, 7>& y, double epsilon, double rho) {
    const array<double, 4> criticalWeight = {0.30, 0.20, 0.35, 0.15};
    const array<double, 3> noncriticalWeight = {0.35, 0.40, 0.25};
    const double alpha = 0.70, beta = 0.30;

    double minFactor = pow(y[0] / 10.0, epsilon);
    double criticalProduct = 1.0, noncriticalProduct = 1.0;
    for (size_t i = 0; i < criticalWeight.size(); ++i) {
        minFactor = min(minFactor, pow(y[i] / 10.0, epsilon));
        criticalProduct *= pow(y[i], criticalWeight[i]);
    }
    for (size_t i = 0; i < noncriticalWeight.size(); ++i) {
        noncriticalProduct *= pow(y[i + 4], noncriticalWeight[i]);
    }
    double criticalPart = minFactor * criticalProduct;
    return pow(alpha * pow(criticalPart, -rho)
             + beta * pow(noncriticalProduct, -rho), -1.0 / rho);
}

int main() {
    const array<double, 5> tWeight = {0.25, 0.15, 0.20, 0.23, 0.17};
    const array<array<double, 5>, 4> tData = {{
        {{6.8, 8.2, 7.8, 6.8, 7.9}},
        {{8.8, 8.9, 9.2, 9.0, 9.3}},
        {{5.6, 5.9, 6.0, 9.0, 5.3}},
        {{4.6, 7.8, 3.8, 5.1, 4.5}}
    }};
    struct Case {
        int system;
        array<double, 7> y;
        double epsilon, rho;
    };
    const array<Case, 8> t3Data = {{
        {1, {{8.3, 7.1, 8.1, 6.9, 9.1, 8.5, 8.6}}, 0.10, 0.10},
        {1, {{7.8, 8.7, 8.0, 6.2, 8.9, 8.0, 8.8}}, 0.05, 0.15},
        {2, {{5.8, 8.1, 6.8, 5.6, 7.9, 6.8, 8.1}}, 0.10, 0.10},
        {2, {{6.8, 7.8, 8.1, 6.9, 8.9, 7.8, 8.8}}, 0.05, 0.15},
        {3, {{3.8, 3.7, 4.8, 4.7, 3.9, 5.8, 6.8}}, 0.10, 0.10},
        {3, {{8.4, 7.2, 8.1, 7.7, 7.9, 0.88, 0.68}}, 0.05, 0.15},
        {4, {{9.0, 8.7, 8.9, 8.6, 9.1, 8.8, 8.9}}, 0.10, 0.10},
        {4, {{8.0, 7.8, 6.8, 8.7, 7.9, 8.1, 8.3}}, 0.05, 0.15}
    }};

    cout << fixed << setprecision(6);
    cout << "Homework 1: T\n";
    for (size_t i = 0; i < tData.size(); ++i)
        cout << "Row " << i + 1 << ": " << modelT(tData[i], tWeight) << '\n';
    cout << "\nHomework 2: T3\n";
    for (size_t i = 0; i < t3Data.size(); ++i) {
        const auto& c = t3Data[i];
        cout << "System " << c.system << ", row " << i % 2 + 1
             << ": " << modelT3(c.y, c.epsilon, c.rho) << '\n';
    }
    return 0;
}
