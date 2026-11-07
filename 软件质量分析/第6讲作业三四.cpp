#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>

using namespace std;

constexpr size_t N = 5;
using Vector = array<double, N>;
using Matrix = array<Vector, N>;

// 作业三的模型 1：子属性加权乘积。
double model1(const Vector& x, const Vector& weight) {
    double result = 1.0;
    for (size_t i = 0; i < N; ++i) {
        result *= pow(x[i], weight[i]);
    }
    return result;
}

// 作业三的模型 2：按照子属性权重及 rho 合成。
double model2(const Vector& x, const Vector& weight, double rho) {
    double sum = 0.0;
    for (size_t i = 0; i < N; ++i) {
        sum += weight[i] * pow(x[i], -rho);
    }
    return pow(sum, -1.0 / rho);
}

Vector normalize(const Vector& v) {
    const double sum = accumulate(v.begin(), v.end(), 0.0);
    Vector result{};
    for (size_t i = 0; i < N; ++i) result[i] = v[i] / sum;
    return result;
}

Vector multiply(const Matrix& a, const Vector& v) {
    Vector result{};
    for (size_t i = 0; i < N; ++i) {
        for (size_t j = 0; j < N; ++j) result[i] += a[i][j] * v[j];
    }
    return result;
}

// EV：幂迭代求最大特征值对应的右特征向量，再归一化。
Vector eigenvectorMethod(const Matrix& a) {
    Vector w{};
    w.fill(1.0 / N);
    for (int iteration = 0; iteration < 100000; ++iteration) {
        const Vector next = normalize(multiply(a, w));
        double difference = 0.0;
        for (size_t i = 0; i < N; ++i)
            difference = max(difference, abs(next[i] - w[i]));
        w = next;
        if (difference < 1e-13) return w;
    }
    throw runtime_error("EV iteration did not converge");
}

// LLSM：每行元素的几何平均数归一化。
Vector logarithmicLeastSquares(const Matrix& a) {
    Vector roots{};
    for (size_t i = 0; i < N; ++i) {
        double product = 1.0;
        for (size_t j = 0; j < N; ++j) product *= a[i][j];
        roots[i] = pow(product, 1.0 / N);
    }
    return normalize(roots);
}

// CSM：对应课件第 49—51 页的迭代过程。
Vector chiSquareMethod(const Matrix& a) {
    const double epsilon = 1e-10;
    Vector w{};
    w.fill(1.0 / N);
    for (int iteration = 0; iteration < 100000; ++iteration) {
        size_t selected = 0;
        double largest = -1.0;
        for (size_t i = 0; i < N; ++i) {
            double value = 0.0;
            for (size_t j = 0; j < N; ++j) {
                value += (1.0 + a[j][i] * a[j][i]) * (w[i] / w[j])
                       - (1.0 + a[i][j] * a[i][j]) * (w[j] / w[i]);
            }
            if (abs(value) > largest) {
                largest = abs(value);
                selected = i;
            }
        }
        if (largest <= epsilon) return w;

        double up = 0.0, bottom = 0.0;
        for (size_t j = 0; j < N; ++j) {
            if (j == selected) continue;
            up += (1.0 + a[selected][j] * a[selected][j]) * (w[j] / w[selected]);
            bottom += (1.0 + a[j][selected] * a[j][selected]) * (w[selected] / w[j]);
        }
        w[selected] *= sqrt(up / bottom);
        w = normalize(w);
    }
    throw runtime_error("CSM iteration did not converge");
}

// 课件中的强度指标 TD：值越小，权重向量越优。
double totalDeviation(const Matrix& a, const Vector& w) {
    double td = 0.0;
    for (size_t i = 0; i < N; ++i)
        for (size_t j = 0; j < N; ++j)
            td += abs(a[i][j] - w[i] / w[j]);
    return td;
}

void printVector(const Vector& v) {
    cout << '(';
    for (size_t i = 0; i < N; ++i) {
        if (i != 0) cout << ", ";
        cout << v[i];
    }
    cout << ')';
}

int main() {
    const Vector attributeWeight = {0.15, 0.20, 0.20, 0.25, 0.20};
    struct Case {
        int system, row;
        Vector x;
        double rho;
    };
    const array<Case, 8> cases = {{
        {1, 1, {{8.6, 9.1, 9.2, 8.8, 8.9}}, 0.01},
        {1, 2, {{8.6, 9.1, 9.2, 8.8, 9.9}}, 0.55},
        {2, 1, {{6.8, 7.9, 5.9, 6.6, 6.1}}, 0.01},
        {2, 2, {{6.8, 7.9, 5.9, 6.6, 6.1}}, 0.55},
        {3, 1, {{9.1, 9.9, 8.9, 8.8, 7.8}}, 0.01},
        {3, 2, {{9.1, 9.9, 8.9, 8.8, 7.8}}, 0.55},
        {4, 1, {{3.5, 4.2, 5.6, 4.9, 5.2}}, 0.01},
        {4, 2, {{3.5, 4.2, 5.6, 4.9, 5.2}}, 0.55}
    }};
    const Matrix a = {{
        {{1.0,     1.0/2, 3.0, 2.0, 1.0/2}},
        {{2.0,     1.0,   2.0, 3.0, 2.0}},
        {{1.0/3,   1.0/2, 1.0, 2.0, 1.0/3}},
        {{1.0/2,   1.0/3, 1.0/2, 1.0, 2.0}},
        {{2.0,     1.0/2, 3.0, 1.0/2, 1.0}}
    }};

    cout << fixed << setprecision(6);
    cout << "Homework 3: attribute measurement\n";
    cout << "System  Row  rho       Model 1       Model 2\n";
    for (const auto& c : cases) {
        cout << setw(6) << c.system << setw(5) << c.row
             << setw(7) << setprecision(2) << c.rho << setprecision(6)
             << setw(14) << model1(c.x, attributeWeight)
             << setw(14) << model2(c.x, attributeWeight, c.rho) << '\n';
    }

    const Vector ev = eigenvectorMethod(a);
    const Vector llsm = logarithmicLeastSquares(a);
    const Vector csm = chiSquareMethod(a);
    const double tdEV = totalDeviation(a, ev);
    const double tdLLSM = totalDeviation(a, llsm);
    const double tdCSM = totalDeviation(a, csm);
    const Vector av = multiply(a, ev);
    const double lambda = accumulate(av.begin(), av.end(), 0.0);
    cout << "\nHomework 4: weight vectors and TD\n";
    cout << "EV   = "; printVector(ev); cout << "  TD = " << tdEV << '\n';
    cout << "LLSM = "; printVector(llsm); cout << "  TD = " << tdLLSM << '\n';
    cout << "CSM  = "; printVector(csm); cout << "  TD = " << tdCSM << '\n';
    cout << "EV largest eigenvalue = " << lambda << '\n';
    if (tdEV <= tdLLSM && tdEV <= tdCSM) cout << "Best by TD: EV\n";
    else if (tdLLSM <= tdCSM) cout << "Best by TD: LLSM\n";
    else cout << "Best by TD: CSM\n";

    cout << "\nPress Enter to exit..." << flush;
    cin.get();
    return 0;
}
