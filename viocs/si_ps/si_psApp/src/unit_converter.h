
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <algorithm>


static const std::string exc_directory("../../exc/");

class UnitConverter {
public:
    UnitConverter(std::string ps_name);
    ~UnitConverter();
    double convert_phys2eng(double value);
    double convert_eng2phys(double value);
private:
    static const int min_name_size = 8;

    bool has_table;
    int row_count;
    double* phys;
    double* eng;

    bool read_interpolation_table(std::string filename);
    double calculate(double x, double* xt, double* yt);
    double interpolate(double x, double* xt, double* yt);
    double extrapolate(double x, double* xt, double* yt);
};
