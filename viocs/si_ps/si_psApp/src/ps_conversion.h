
#include <stdio.h>
#include <string.h>

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <algorithm>

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>


static const std::string exc_directory("../../exc/");

class UnitConverter {
public:
    UnitConverter(std::string ps_name);
    ~UnitConverter();
    // double convert_phys2eng(double value);
    // double convert_eng2phys(double value);
private:
    static const int min_name_size = 8;
    bool has_table;
    unsigned int row_count;
    double* phys;
    double* eng;
    //
    bool read_interpolation_table(std::string filename);
    // InterpolationTable(std::string filename);
    // ~InterpolationTable();
    // double calculate(double value);
    // double interpolate(double value, double* xt, double* yt);
    // double extrapolate(double value, double* xt, double* yt);
};
