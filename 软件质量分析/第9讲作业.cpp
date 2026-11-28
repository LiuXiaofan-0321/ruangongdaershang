#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

struct Category {
    string name;
    vector<int> counts;                   // 按作业表列序输入实例数
    vector<vector<int>> risk0, risk10;    // 每项保留全部证据
};

const vector<Category> homework = {
    {"MEM", {2,7,1,1,3,3,3,1,1,2,2,1,1,4,7},
     {{4},{4,1},{1},{1,4},{1},{1},{4},{1,1},{1},{1},{4,1},{1,1},{1,4},{1},{4}},
     {{4},{4,7},{7},{4,4},{9},{4},{7},{4,7},{7},{4},{7,7},{7,4},{7,4},{9},{7}}},
    {"STO", {1,1,1,1}, {{1,4},{1,1},{4},{4}}, {{4,7},{7,9},{7},{7}}},
    {"LOG", {2,1,1,2,1,1,1}, {{1},{1},{4},{1},{1},{1},{7}}, {{7},{10},{7},{4},{7},{10},{9}}},
    {"NUM", {1,2}, {{4},{1}}, {{7},{4}}},
    {"ARU", {1,3}, {{1},{1,4}}, {{7},{7,7}}}
};

// Brassard 优先顺序矩阵对角线留空，再将各行之和归一化。
vector<double> weights(const vector<int>& counts) {
    if (counts.size() == 1) return {1.0};
    vector<double> sums(counts.size(), 0.0);
    for (size_t i = 0; i < counts.size(); ++i)
        for (size_t j = 0; j < counts.size(); ++j)
            if (i != j) sums[i] += static_cast<double>(counts[i]) / counts[j];
    double total = accumulate(sums.begin(), sums.end(), 0.0);
    for (double& x : sums) x /= total;
    return sums;
}

double entropy(const vector<vector<int>>& evidence, const vector<double>& beta) {
    double h = 0;
    for (size_t j = 0; j < evidence.size(); ++j) {
        int risk = *max_element(evidence[j].begin(), evidence[j].end());
        h += beta[j] * log10(risk);
    }
    return h;
}

vector<Category> readInput() {
    cout << "Number of categories (1-5), then one ID and its counts per row:\n";
    int n;
    if (!(cin >> n) || n < 1 || n > 5) throw runtime_error("Invalid category count");
    vector<Category> result;
    set<string> seen;
    for (int i = 0; i < n; ++i) {
        string id;
        cin >> id;
        auto it = find_if(homework.begin(), homework.end(),
                          [&](const Category& c) { return c.name == id; });
        if (it == homework.end() || !seen.insert(id).second)
            throw runtime_error("Unknown or duplicate category: " + id);
        Category c = *it;
        for (int& count : c.counts)
            if (!(cin >> count) || count <= 0) throw runtime_error("Expected positive case count");
        result.push_back(c);
    }
    return result;
}

void calculate(const vector<Category>& categories) {
    vector<int> sizes;
    for (const auto& c : categories) sizes.push_back(static_cast<int>(c.counts.size()));
    auto theta = weights(sizes);
    array<double, 2> software = {1.0, 1.0};
    cout << fixed << setprecision(6);
    cout << "Class      theta        H(0)        U(0)       H(10)       U(10)\n";
    for (size_t i = 0; i < categories.size(); ++i) {
        const auto& c = categories[i];
        auto beta = weights(c.counts);
        cout << left << setw(5) << c.name << right << setw(11) << theta[i];
        for (int t = 0; t < 2; ++t) {
            double h = entropy(t == 0 ? c.risk0 : c.risk10, beta);
            double u = max(1.0, 10.0 * exp(-h));
            software[t] *= pow(u, theta[i]);
            cout << setw(12) << h << setw(12) << u;
        }
        cout << '\n';
    }
    cout << "T(0)  = " << software[0] << "\nT(10) = " << software[1] << '\n';
}

int main(int argc, char* argv[]) {
    int status = 0;
    try {
        if (argc == 1) calculate(homework);
        else if (argc == 2 && string(argv[1]) == "--input") calculate(readInput());
        else throw runtime_error("Usage: run without arguments or use --input");
    } catch (const exception& e) {
        cerr << e.what() << '\n';
        status = 1;
    }
    cout.flush();
    system("pause");
    return status;
}
