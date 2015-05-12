
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <algorithm>
#include <stdlib.h>


static const std::string exc_directory("../../exc/");

class UnitConverter {
public:
    UnitConverter(std::string ps_name);
    ~UnitConverter();
    double convert_phys2eng(double value, double noise_level);
    double convert_eng2phys(double value, double noise_level);
private:
    bool has_table;
    int row_count;
    double* phys;
    double* eng;

    std::string get_ps_name(std::string conv_record_name);
    bool read_interpolation_table(std::string filename);
    double calculate(double x, double* xt, double* yt);
    double interpolate(double x, double* xt, double* yt);
    double extrapolate(double x, double* xt, double* yt);
    double get_random();
};
