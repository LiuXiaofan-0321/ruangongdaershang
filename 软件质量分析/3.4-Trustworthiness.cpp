#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>

constexpr std::size_t attributeCount = 9;
constexpr std::size_t subattributeCount = 28;
using AttributeScores = std::array<double, attributeCount>;
using SubattributeScores = std::array<double, subattributeCount>;

struct Attribute {
    const char* name;
    double weight;
    std::size_t subattributeCount;
};

constexpr std::array<Attribute, attributeCount> attributes = {{
    {"Overall planning and execution",        0.05, 3},
    {"Analysis and design",                   0.17, 3},
    {"Test and verification",                 0.20, 6},
    {"Reliability and safety",                0.15, 3},
    {"Technical state changes",               0.09, 3},
    {"Quality issue closure and prevention",  0.09, 2},
    {"Configuration management",             0.11, 3},
    {"Software development environment",      0.05, 2},
    {"Third-party evaluation",                0.09, 3}
}};

constexpr SubattributeScores subattributeWeights = {
    0.31, 0.36, 0.33,
    0.33, 0.33, 0.34,
    0.16, 0.17, 0.17, 0.17, 0.17, 0.16,
    0.33, 0.34, 0.33,
    0.34, 0.33, 0.33,
    0.50, 0.50,
    0.33, 0.34, 0.33,
    0.50, 0.50,
    0.33, 0.33, 0.34
};

AttributeScores calculateAttributes(const SubattributeScores& means) {
    AttributeScores scores{};
    std::size_t column = 0;
    for (std::size_t i = 0; i < attributes.size(); ++i) {
        double product = 1.0;
        for (std::size_t j = 0; j < attributes[i].subattributeCount; ++j, ++column) {
            product *= std::pow(means[column], subattributeWeights[column]);
        }
        scores[i] = std::round(product * 100000.0) / 100000.0;
    }
    return scores;
}

double softwareScore(const AttributeScores& scores) {
    double product = 1.0;
    for (std::size_t i = 0; i < attributes.size(); ++i) {
        product *= std::pow(scores[i], attributes[i].weight);
    }
    return product;
}

int countBelow(const AttributeScores& scores, double threshold) {
    return static_cast<int>(std::count_if(scores.begin(), scores.end(),
        [threshold](double value) { return value < threshold; }));
}

const char* trustworthinessGrade(double total, const AttributeScores& scores) {
    constexpr int maxBelowThreshold = 3;
    if (total >= 9.5 && countBelow(scores, 9.5) <= maxBelowThreshold
                     && countBelow(scores, 8.5) == 0) {
        return "V";
    }
    if (total >= 8.5 && countBelow(scores, 8.5) <= maxBelowThreshold
                     && countBelow(scores, 7.0) == 0) {
        return "IV";
    }
    if (total >= 7.0 && countBelow(scores, 7.0) <= maxBelowThreshold
                     && countBelow(scores, 4.5) == 0) {
        return "III";
    }
    if (total >= 4.5 && countBelow(scores, 4.5) <= maxBelowThreshold) {
        return "II";
    }
    return "I";
}

int main() {
    // 第四题数据.xlsx，Sheet1!B3:AC4，已是十位专家评分的均值。
    constexpr SubattributeScores id1Means = {
        8.1, 8.1, 8.6,
        8.7, 9.4, 7.8,
        8.7, 7.9, 7.8, 7.0, 7.5, 9.3,
        8.1, 8.6, 8.8,
        9.1, 8.9, 8.6,
        9.0, 8.7,
        8.6, 8.7, 8.0,
        9.3, 9.0,
        9.3, 9.3, 9.1
    };
    constexpr SubattributeScores id2Means = {
        8.7, 7.6, 7.97,
        9.0, 7.7, 8.9,
        7.6, 8.5, 8.3, 7.3, 6.6, 7.2,
        9.2, 7.9, 8.8,
        8.9, 8.9, 8.8,
        9.2, 8.8,
        8.9, 8.4, 8.5,
        9.0, 8.1,
        8.8, 7.8, 9.5
    };

    const AttributeScores id1 = calculateAttributes(id1Means);
    const AttributeScores id2 = calculateAttributes(id2Means);
    const double id1Total = softwareScore(id1);
    const double id2Total = softwareScore(id2);

    std::cout << "3.4 Software trustworthiness at delivery review\n"
              << "y_i = product(x_ij^w_ij), T = product(y_i^alpha_i)\n\n"
              << std::left << std::setw(40) << "Attribute"
              << std::right << std::setw(12) << "ID1" << std::setw(12) << "ID2" << '\n'
              << std::fixed << std::setprecision(5);
    for (std::size_t i = 0; i < attributes.size(); ++i) {
        std::cout << std::left << std::setw(40) << attributes[i].name
                  << std::right << std::setw(12) << id1[i] << std::setw(12) << id2[i] << '\n';
    }
    std::cout << '\n' << std::left << std::setw(40) << "Attributes below 8.5"
              << std::right << std::setw(12) << countBelow(id1, 8.5)
              << std::setw(12) << countBelow(id2, 8.5) << '\n'
              << std::left << std::setw(40) << "Attributes below 7.0"
              << std::right << std::setw(12) << countBelow(id1, 7.0)
              << std::setw(12) << countBelow(id2, 7.0) << '\n'
              << std::setprecision(3)
              << std::left << std::setw(40) << "Software trustworthiness T"
              << std::right << std::setw(12) << id1Total << std::setw(12) << id2Total << '\n'
              << std::left << std::setw(40) << "Trustworthiness grade"
              << std::right << std::setw(12) << trustworthinessGrade(id1Total, id1)
              << std::setw(12) << trustworthinessGrade(id2Total, id2) << "\n\n"
              << std::flush;
    std::system("pause");
}
