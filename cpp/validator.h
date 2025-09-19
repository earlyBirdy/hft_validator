#pragma once
#include <cmath>
#include <deque>

struct Validator {
    virtual bool validate(double price, uint64_t ts_ns) = 0;
    virtual ~Validator() = default;
};

struct EWMAValidator : public Validator {
    double mean = 0.0, var = 1.0;
    bool init = false;
    double alpha;
    double threshold;
    EWMAValidator(double alpha_=0.05, double thr=2.5) : alpha(alpha_), threshold(thr) {}
    bool validate(double price, uint64_t) override {
        if (!init) { mean = price; init = true; return false; }
        double delta = price - mean;
        mean += alpha * delta;
        var = (1 - alpha) * (var + alpha * delta * delta);
        double stddev = std::sqrt(var);
        double z = (price - mean) / (1e-9 + stddev);
        return std::fabs(z) > threshold;
    }
};

struct VolatilityValidator : public Validator {
    std::deque<double> window;
    int maxSize;
    double maxVol;
    VolatilityValidator(int win=50, double maxV=0.02) : maxSize(win), maxVol(maxV) {}
    bool validate(double price, uint64_t) override {
        window.push_back(price);
        if ((int)window.size() > maxSize) window.pop_front();
        if (window.size() < 2) return false;
        double mean = 0;
        for (auto v : window) mean += v;
        mean /= window.size();
        double var = 0;
        for (auto v : window) var += (v - mean) * (v - mean);
        var /= window.size();
        double stddev = std::sqrt(var);
        return stddev < maxVol;
    }
};

struct ImbalanceValidator : public Validator {
    double threshold;
    ImbalanceValidator(double thr=0.6) : threshold(thr) {}
    bool validate(double price, uint64_t ts_ns) override {
        double imbalance = (fmod(price, 2.0) > 1.0) ? 0.7 : 0.4;
        return imbalance > threshold;
    }
};

struct PersistenceValidator : public Validator {
    int holdTicks;
    int counter = 0;
    bool active = false;
    PersistenceValidator(int h=3) : holdTicks(h) {}
    bool validate(double price, uint64_t ts_ns) override {
        if (price > 100.0) {
            counter++;
            if (counter >= holdTicks) { active = true; }
        } else {
            counter = 0;
            active = false;
        }
        return active;
    }
};
