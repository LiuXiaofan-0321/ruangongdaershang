#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;
using Vector = vector<double>;
using Matrix = vector<Vector>;

// 课件各权重求法都将权重向量归一化。
Vector normalize(Vector w) {
    double sum = accumulate(w.begin(), w.end(), 0.0);
    for (double& x : w) x /= sum;
    return w;
}

Vector multiply(const Matrix& a, const Vector& w) {
    Vector result(w.size(), 0.0);
    for (size_t i = 0; i < w.size(); ++i)
        for (size_t j = 0; j < w.size(); ++j)
            result[i] += a[i][j] * w[j];
    return result;
}

// EV：幂迭代求最大特征值对应的右特征向量。
Vector eigenvectorMethod(const Matrix& a) {
    const size_t n = a.size();
    Vector w(n, 1.0 / n);
    for (int k = 0; k < 100000; ++k) {
        Vector next = normalize(multiply(a, w));
        double delta = 0.0;
        for (size_t i = 0; i < n; ++i) delta = max(delta, abs(next[i] - w[i]));
        w = next;
        if (delta < 1e-13) return w;
    }
    throw runtime_error("EV did not converge");
}

// LLSM：各行的几何平均数归一化。
Vector logarithmicLeastSquares(const Matrix& a) {
    const size_t n = a.size();
    Vector result(n, 1.0);
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) result[i] *= a[i][j];
        result[i] = pow(result[i], 1.0 / n);
    }
    return normalize(result);
}

// 按第6讲课件第49—51页的 CSM 迭代代码计算。
Vector chiSquareMethod(const Matrix& a) {
    const size_t n = a.size();
    Vector w(n, 1.0 / n);
    for (int k = 0; k < 100000; ++k) {
        size_t m = 0;
        double largest = -1.0;
        for (size_t i = 0; i < n; ++i) {
            double d = 0.0;
            for (size_t j = 0; j < n; ++j) {
                d += (1 + a[j][i] * a[j][i]) * w[i] / w[j]
                   - (1 + a[i][j] * a[i][j]) * w[j] / w[i];
            }
            if (abs(d) > largest) {
                largest = abs(d);
                m = i;
            }
        }
        if (largest <= 1e-10) return w;
        double up = 0.0, down = 0.0;
        for (size_t j = 0; j < n; ++j) {
            if (j == m) continue;
            up += (1 + a[m][j] * a[m][j]) * w[j] / w[m];
            down += (1 + a[j][m] * a[j][m]) * w[m] / w[j];
        }
        w[m] *= sqrt(up / down);
        w = normalize(w);
    }
    throw runtime_error("CSM did not converge");
}

double totalDeviation(const Matrix& a, const Vector& w) {
    double td = 0.0;
    for (size_t i = 0; i < w.size(); ++i)
        for (size_t j = 0; j < w.size(); ++j)
            td += abs(a[i][j] - w[i] / w[j]);
    return td;
}

struct WeightResult {
    string method;
    Vector w;
    double td;
};

vector<WeightResult> allWeights(const Matrix& a) {
    vector<WeightResult> result = {
        {"EV", eigenvectorMethod(a), 0.0},
        {"LLSM", logarithmicLeastSquares(a), 0.0},
        {"CSM", chiSquareMethod(a), 0.0}
    };
    for (WeightResult& r : result) r.td = totalDeviation(a, r.w);
    return result;
}

const WeightResult& bestByTD(const vector<WeightResult>& results) {
    return *min_element(results.begin(), results.end(),
        [](const WeightResult& x, const WeightResult& y) { return x.td < y.td; });
}

double geometricGroupScore(const Vector& values, const Vector& w) {
    double result = 1.0;
    for (size_t i = 0; i < values.size(); ++i) result *= pow(values[i], w[i]);
    return result;
}

int below(const Vector& values, double threshold) {
    return static_cast<int>(count_if(values.begin(), values.end(),
        [threshold](double value) { return value < threshold; }));
}

// 属性值题目未提供，因此用参数分别计算满足和不满足属性条件的等级。
int grade(double t, const Vector& critical, const Vector& all,
          bool allAttributesAtLeast45) {
    const int n = static_cast<int>(critical.size());
    const int maxLow = n - (2 * n + 2) / 3;  // n - ceil(2n/3)
    if (t >= 9.5 && below(critical, 9.5) <= maxLow && below(all, 8.5) == 0) return 5;
    if (t >= 8.5 && below(critical, 8.5) <= maxLow && below(all, 7.0) == 0) return 4;
    if (t >= 7.0 && below(critical, 7.0) <= maxLow && allAttributesAtLeast45) return 3;
    if (t >= 4.5 && below(critical, 4.5) <= maxLow) return 2;
    return 1;
}

void printTD(const vector<WeightResult>& results) {
    for (const WeightResult& r : results) cout << ' ' << r.method << '=' << r.td;
    cout << '\n';
}

void printWeights(const Vector& w, int first) {
    for (size_t i = 0; i < w.size(); ++i) {
        cout << "CP" << first + static_cast<int>(i) << '=' << w[i];
        if (i + 1 == w.size() || (i + 1) % 4 == 0) cout << '\n';
        else cout << "  ";
    }
}

void printNonreciprocal(const Matrix& a, int first) {
    for (size_t i = 0; i < a.size(); ++i) {
        for (size_t j = i + 1; j < a.size(); ++j) {
            if (abs(a[i][j] * a[j][i] - 1.0) > 1e-10) {
                cout << "CP" << first + static_cast<int>(i)
                     << "/CP" << first + static_cast<int>(j)
                     << ": " << a[i][j] << " * " << a[j][i] << " != 1\n";
            }
        }
    }
}

int main() {
    // 关键组件 CP1—CP5 的判断矩阵。
    const Matrix criticalMatrix = {
        {1, 2, 1.0/2, 2, 1.0/4},
        {1.0/2, 1, 2, 3, 1.0/2},
        {2, 1.0/2, 1, 1, 1.0/2},
        {1.0/2, 1.0/3, 1, 1, 1.0/2},
        {4, 2, 2, 2, 1}
    };
    // 非关键组件 CP6—CP13，保留课件原始矩阵。
    const Matrix noncriticalMatrix = {
        {1, 3, 2, 1.0/2, 2, 1, 3, 3},
        {1.0/3, 1, 2, 1, 2, 2, 2, 2},
        {1.0/2, 1.0/2, 1, 1.0/2, 1, 1.0/2, 3, 3},
        {2, 1, 2, 1, 3, 1.0/2, 3, 3},
        {1.0/2, 1.0/2, 1, 1.0/3, 1, 1, 2, 2},
        {1, 1.0/2, 2, 2, 1, 1, 2, 2},
        {1.0/3, 1.0/2, 1, 1.0/3, 1.0/2, 1.0/2, 1, 2},
        {1.0/3, 1.0/2, 2, 1.0/3, 1.0/2, 1.0/2, 1.0/2, 1}
    };
    const Vector criticalValues = {8.430, 8.530, 6.042, 9.094, 8.289};
    const Vector noncriticalValues = {6.192, 8.020, 7.984, 8.713,
                                      9.211, 7.777, 7.897, 8.075};
    Vector allValues = criticalValues;
    allValues.insert(allValues.end(), noncriticalValues.begin(), noncriticalValues.end());

    const auto criticalResults = allWeights(criticalMatrix);
    const auto noncriticalResults = allWeights(noncriticalMatrix);
    const auto& cw = bestByTD(criticalResults);
    const auto& nw = bestByTD(noncriticalResults);
    const double criticalScore = geometricGroupScore(criticalValues, cw.w);
    const double noncriticalScore = geometricGroupScore(noncriticalValues, nw.w);

    cout << fixed << setprecision(6);
    cout << "Critical group TD:"; printTD(criticalResults);
    cout << "Selected: " << cw.method << '\n';
    printWeights(cw.w, 1);
    cout << "Noncritical group TD:"; printTD(noncriticalResults);
    cout << "Selected: " << nw.method << '\n';
    printWeights(nw.w, 6);
    cout << "Critical score: " << criticalScore << '\n';
    cout << "Noncritical score: " << noncriticalScore << '\n';
    cout << "\nalpha  beta    T          Grade if attributes >= 4.5 / not\n";
    for (double alpha : {0.70, 0.60, 0.55}) {
        const double beta = 1.0 - alpha;
        const double t = alpha * criticalScore + beta * noncriticalScore;
        cout << setprecision(2) << alpha << "   " << beta << "   "
             << setprecision(6) << t << "   "
             << grade(t, criticalValues, allValues, true) << " / "
             << grade(t, criticalValues, allValues, false) << '\n';
    }
    cout << "\nNonreciprocal pairs in the original matrix:\n";
    printNonreciprocal(noncriticalMatrix, 6);
    cout << "Results require confirmation of the matrix and attributes.\n";
    cout << "\nPress Enter to exit..." << flush;
    cin.get();
    return 0;
}
