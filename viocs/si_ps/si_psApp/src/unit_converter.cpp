
#include "unit_converter.h"


UnitConverter::UnitConverter(std::string record_name)
{
    std::string ps_name = get_ps_name(record_name);
    std::cout << ps_name << '\n';
    if (ps_name.size() == 0)
        has_table = false;
    else
        has_table = read_interpolation_table(ps_name);
}

UnitConverter::~UnitConverter()
{
    if (has_table) {
        delete [] phys;
        delete [] eng;
    }
}

double UnitConverter::convert_phys2eng(double value, double noise_level)
{
    double output = calculate(value, phys, eng);
    return output + noise_level*get_random();
}

double UnitConverter::convert_eng2phys(double value, double noise_level)
{
    double output = calculate(value, eng, phys);
    return output + noise_level*get_random();
}

std::string UnitConverter::get_ps_name(std::string conv_record_name)
{
    const char sep = '-';

    // Ignore "-X" and "-Y" in record name (get only middle part)
    std::size_t ps = conv_record_name.find(sep);
    std::size_t pe = conv_record_name.rfind(sep);

    if (ps<conv_record_name.size()-1 && pe>ps)
        return conv_record_name.substr(ps+1, pe-ps-1);
    else
        return std::string("");
}

bool UnitConverter::read_interpolation_table(std::string filename)
{
    // std::cout << "Reading table for " << filename << "\n";

    std::string fullname = exc_directory + filename;

    // std::cout << "Fullname is " << fullname << "\n";

    std::ifstream fp(fullname.c_str());
	if (fp.fail())
        return false;

    int row = 0;
    std::string line, s;

    // Read row count
    while (std::getline(fp, line)) {
        if (line[0] == '#')
            continue;
        else {
            std::istringstream ss(line);
            ss >> row_count;
            break;
        }
    }

    // std::cout << "Row count is " << row_count << "\n";

    if (row_count < 2)
        return false;

    phys = new double[row_count];
    eng = new double[row_count];

    // Read row values
    while (std::getline(fp, line) && row<row_count) {
        if (line[0] == '#')
            continue;
        else {
            // std::cout << "line is: " << line << '\n';
            std::istringstream ss(line);
            ss >> eng[row];
            ss >> phys[row];
            // std::cout << "eng, phys: " << eng[row] << ", " << phys[row] << "\n";
            ++row;
        }
    }

    if (row_count != row) {
        std::cout << "Truncating row count at " << row << '\n';
        row_count = row;
    }

    return true;
}

double UnitConverter::calculate(double x, double* xt, double* yt)
{
    if (has_table) {
        if (x>=xt[0] && x<xt[row_count-1])
            return interpolate(x, xt, yt);
        else
            return extrapolate(x, xt, yt);
    } else
        return x;
}

double UnitConverter::interpolate(double x, double* xt, double* yt)
{
    int i;
    double xa, xb, ya, yb, dx, dy, y;

    for (i=0; i<row_count-1; ++i)
        if (x < xt[i+1])
            break;

    xa = xt[i];
    xb = xt[i+1];
    ya = yt[i];
    yb = yt[i+1];
    dx = xb - xa;
    dy = yb - ya;

    y = ya + (x - xa)*dy/dx;

    return y;
}

double UnitConverter::extrapolate(double x, double* xt, double* yt){
    double dx, dy, y;

    if (x < xt[0]) {
        dx = xt[1] - xt[0];
        dy = yt[1] - yt[0];
        y = yt[0] + (x - xt[0])*dy/dx;
    } else {
        dx = xt[row_count-1] - xt[row_count-2];
        dy = yt[row_count-1] - yt[row_count-2];
        y = yt[row_count-1] + (x - xt[row_count-1])*dy/dx;
    }

    return y;
}

double UnitConverter::get_random()
{
    // Return random double between -1.0 and 1.0
    return 2*(double)rand()/RAND_MAX - 1.0;
}
