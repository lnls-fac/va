/*
 * Conversion of power supply values using excitation tables.
 */


#include "ps_conversion.h"


// #define MAXINTERPTABLESIZE 1000
// #define MAXLINESIZE 80
//
//
// static const int max_str_size = 160;
//
// static bool has_table = false;
// static int num_pts = 0;
// static double phys[MAXINTERPTABLESIZE], eng[MAXINTERPTABLESIZE];
//
// static bool read_interpolation_table(char* name, double* xt, double* yt);
// static double calculate(double x, double* xt, double* yt);
// static double interpolate(double x, double* xt, double* yt);
// static double extrapolate(double x, double* xt, double* yt);


UnitConverter::UnitConverter(std::string record_name)
{
    int size = record_name.size();

    std::cout << record_name << '\n';
    if (size <= min_name_size)
        has_table = false;
    else {
        // Ignore "CONV-" and "-XX" in record name
        std::string ps_name = record_name.substr(5, size-8);
        has_table = read_interpolation_table(ps_name);
    }
}

UnitConverter::~UnitConverter()
{
    if (has_table) {
        delete [] phys;
        delete [] eng;
    }
}

bool UnitConverter::read_interpolation_table(std::string filename)
{
    std::cout << "Reading table for " << filename << "\n";

    std::string fullname = exc_directory + filename;

    std::cout << "Fullname is " << fullname << "\n";

    std::ifstream fp(fullname.c_str());
	if (fp.fail())
        return false;

    std::cout << "Success!\n";

    unsigned int row = 0;
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

    std::cout << "Row count is " << row_count << "\n";

    if (row_count < 2)
        return false;

    phys = new double[row_count];
    eng = new double[row_count];

    // Read row values
    while (std::getline(fp, line) && row<row_count) {
        if (line[0] == '#')
            continue;
        else {
            std::cout << "line is: " << line << '\n';
            std::istringstream ss(line);
            ss >> eng[row];
            ss >> phys[row];
            std::cout << "eng, phys: " << eng[row] << ", " << phys[row] << "\n";
            ++row;
        }
    }

    if (row_count != row) {
        std::cout << "Truncating row count at " << row << '\n';
        row_count = row;
    }

    return true;
}

long ps_conversion_init(struct subRecord *psub)
{
    UnitConverter u(psub->name);

    // char ps_name[max_str_size];
    // int n;
    //
    //
    //
    //
    // /*
    //  * Record name must have the form CONV-...-XX, where XX can be RB or SP.
    //  * Remove "CONV-" from start and "-XX" from end.
    //  */
    // n = strlen(psub->name);
    // if (n>8 && n<max_str_size) {
    //     strncpy(ps_name, psub->name+5, n-8);
    //     ps_name[n-8] = '\0';
    //     printf("%s\n", ps_name);
    //     has_table = read_interpolation_table(ps_name, eng, phys);
    // } else
    //     has_table = false;

    return 0;
}

long ps_conversion_phys2eng_process(struct subRecord *psub)
{
    // if (has_table)
    //     psub->b = calculate(psub->a, phys, eng);
    // else
    //     psub->b = psub->a;

    return 0;
}

// static bool read_interpolation_table(char* name, double* xt, double* yt)
// {
//     FILE* fp;
//     char fullname[160] = "/home/fac_files/code/va/viocs/si_ps/si_psApp/src/";
//
//     strcat(fullname, name);
//     fp = fopen(fullname, "r");
//     if (fp == NULL) {
//         printf("Interpolation table for %s not found.\n", name);
//         return false;
//     } else
//         printf("FOUND %s!\n", fullname);
//
//
//     char line[MAXLINESIZE];
//     double x, y;
//     int i, n;
//
//     i = 0;
//     while(fgets(line, MAXLINESIZE, fp) != NULL) {
//         if (line[0] == '#')
//             continue;
//
//         n = sscanf(line, "%lf %lf", &x, &y);
//         if (n != 2)
//             continue;
//
//         xt[i] = x;
//         yt[i] = y;
//
//         i++;
//     }
//
//     num_pts = i;
//
//     for (i=0; i<num_pts; ++i)
//         printf("x: %7.3f, y: %7.3f\n", xt[i], yt[i]);
//
//     if (num_pts > 0)
//         return true;
//     else
//         return false;
// }
//
// static double calculate(double x, double* xt, double* yt)
// {
//     if (x>=xt[0] && x<xt[num_pts-1])
//         return interpolate(x, xt, yt);
//     else
//         return extrapolate(x, xt, yt);
// }
//
// static double interpolate(double x, double* xt, double* yt)
// {
//     int i;
//     double xa, xb, ya, yb, dx, dy, y;
//
//     for (i=0; i<num_pts-1; ++i)
//         if (x < xt[i+1])
//             break;
//
//     xa = xt[i];
//     xb = xt[i+1];
//     ya = yt[i];
//     yb = yt[i+1];
//     dx = xb - xa;
//     dy = yb - ya;
//
//     y = ya + (x - xa)*dy/dx;
//
//     return y;
// }
//
// static double extrapolate(double x, double* xt, double* yt)
// {
//     double dx, dy, y;
//
//     if (x < xt[0]) {
//         dx = xt[1] - xt[0];
//         dy = yt[1] - yt[0];
//         y = yt[0] + (x - xt[0])*dy/dx;
//     } else {
//         dx = xt[num_pts-1] - xt[num_pts-2];
//         dy = yt[num_pts-1] - yt[num_pts-2];
//         y = yt[num_pts-1] + (x - xt[num_pts-1])*dy/dx;
//     }
//
//     return y;
// }

epicsRegisterFunction(ps_conversion_init);
epicsRegisterFunction(ps_conversion_phys2eng_process);
