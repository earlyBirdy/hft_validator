#include "validator.h"
#include <vector>
#include <iostream>
#include <cstdlib>

struct Tick { uint64_t ts_ns; double price; };

int main() {
    std::vector<Tick> ticks;
    for (int i = 0; i < 1000; i++) {
        ticks.push_back({1000ull * i, 100.0 + (rand() % 20) / 10.0});
    }
    EWMAValidator v1(0.05, 2.5);
    VolatilityValidator v2(50, 0.05);
    int trades1=0, trades2=0;
    for (auto &t : ticks) {
        if (v1.validate(t.price, t.ts_ns)) trades1++;
        if (v2.validate(t.price, t.ts_ns)) trades2++;
    }
    std::cout << "EWMA trades: " << trades1 << "\n";
    std::cout << "Volatility trades: " << trades2 << "\n";
    return 0;
}
