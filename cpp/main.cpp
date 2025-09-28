#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <fstream>
#include <cmath>
#include <stdexcept>

struct Tick { std::string t; double p; };

static std::vector<Tick> load_csv(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("Failed to open CSV: " + path);
    std::vector<Tick> ticks;
    std::string line;
    bool header = true;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string t, pstr;
        if (!std::getline(ss, t, ',')) continue;
        if (!std::getline(ss, pstr, ',')) continue;
        if (header && t.find("time") != std::string::npos) { header = false; continue; }
        try {
            double p = std::stod(pstr);
            ticks.push_back({t, p});
        } catch (...) {}
    }
    return ticks;
}

static std::string getArg(int argc, char** argv, const std::string& key, const std::string& def="") {
    for (int i=1;i<argc;i++){
        std::string a(argv[i]);
        auto pos = a.find('=');
        if (pos!=std::string::npos && a.substr(0,pos)==key) return a.substr(pos+1);
    }
    return def;
}

struct Result {
    double pnl = 0.0;
    int trades = 0;
    int wins = 0;
    double max_dd = 0.0;
    double sharpe = 0.0;
};

static Result run_ewma(const std::vector<Tick>& ticks, int window, double alpha, double threshold) {
    if (ticks.size() < (size_t)window+2) throw std::runtime_error("Not enough data for EWMA");
    double ewma = ticks[0].p;
    double var = 0.0;
    double pnl = 0.0;
    double peak = 0.0;
    double min_equity = 0.0;
    int pos = 0;
    int trades = 0, wins = 0;
    std::vector<double> rets;

    for (size_t i=1;i<ticks.size();++i) {
        double px = ticks[i].p;
        double prev_px = ticks[i-1].p;
        double ret = (px - prev_px);
        rets.push_back(ret);

        ewma = alpha*px + (1.0-alpha)*ewma;
        double diff = px - ewma;
        var = (1.0 - alpha)*(var + alpha*diff*diff);

        double vol = std::sqrt(std::max(var, 1e-12));
        double upper = ewma + threshold*vol;
        double lower = ewma - threshold*vol;

        int new_pos = 0;
        if (px > upper) new_pos = +1;
        else if (px < lower) new_pos = -1;
        else new_pos = pos;

        if (new_pos != pos) {
            trades++;
            if ((pos==+1 && ret>0) || (pos==-1 && ret<0)) wins++;
        }

        pnl += pos * ret;
        peak = std::max(peak, pnl);
        min_equity = std::min(min_equity, pnl);
        pos = new_pos;
    }

    double mean = 0.0, var_r = 0.0;
    if (!rets.empty()) {
        for (auto r: rets) mean += r;
        mean /= rets.size();
        for (auto r: rets) var_r += (r-mean)*(r-mean);
        var_r /= (rets.size()>1? (rets.size()-1): 1);
    }
    double sharpe = (std::sqrt((double)rets.size()) * (var_r>0? mean/std::sqrt(var_r): 0.0));

    Result R;
    R.pnl = pnl;
    R.trades = trades;
    R.wins = wins;
    R.max_dd = peak - min_equity;
    R.sharpe = sharpe;
    return R;
}

int main(int argc, char** argv) {
    std::string data = getArg(argc, argv, "--data", "data/sample_prices.csv");
    std::string validator = getArg(argc, argv, "--validator", "EWMA");
    int window = std::stoi(getArg(argc, argv, "--window", "50"));
    double alpha = std::stod(getArg(argc, argv, "--alpha", "0.05"));
    double threshold = std::stod(getArg(argc, argv, "--threshold", "2.5"));

    auto ticks = load_csv(data);

    Result R;
    if (validator == "EWMA") {
        R = run_ewma(ticks, window, alpha, threshold);
    } else {
        std::cerr << "Unknown validator: " << validator << ", falling back to EWMA\n";
        R = run_ewma(ticks, window, alpha, threshold);
    }

    std::cout << "{"
              << "\"validator\":\"" << validator << "\","
              << "\"window\":" << window << ","
              << "\"alpha\":" << alpha << ","
              << "\"threshold\":" << threshold << ","
              << "\"pnl\":" << R.pnl << ","
              << "\"trades\":" << R.trades << ","
              << "\"wins\":" << R.wins << ","
              << "\"max_dd\":" << R.max_dd << ","
              << "\"sharpe\":" << R.sharpe
              << "}" << std::endl;
    return 0;
}
