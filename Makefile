CXX=g++
CXXFLAGS=-O2 -std=c++17

all: backtester

backtester: cpp/main.cpp
	$(CXX) $(CXXFLAGS) -o backtester cpp/main.cpp

clean:
	rm -f backtester
