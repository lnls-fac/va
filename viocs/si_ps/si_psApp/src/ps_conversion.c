/*
 * Conversion of power supply values using excitation tables.
 */


#include <stdio.h>

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

#define true 1
#define false 0
#define MAXTABSIZE 100


typedef int bool;

static int has_table;
static int num_pts;
static double phys[MAXTABSIZE], eng[MAXTABSIZE];

static bool read_interpolation_table(char* name, double* xt, double* yt);
static double calculate(double x, double* xt, double* yt);
static double interpolate(double x, double* xt, double* yt);
static double extrapolate(double x, double* xt, double* yt);

long ps_conversion_init(struct subRecord *psub)
{
    has_table = read_interpolation_table(psub->name, phys, eng);
    return 0;
}

long ps_conversion_phys2eng_process(struct subRecord *psub)
{
    if (has_table)
        psub->b = calculate(psub->a, phys, eng);
    else
        psub->b = psub->a;

    return 0;
}

static int read_interpolation_table(char* name, double* xt, double* yt)
{
    num_pts = 2;

    xt[0] = 0.0;
    xt[1] = 1.0;
    yt[0] = 0.5;
    yt[1] = 2.5;

    return true;
    //return false;
}

static double calculate(double x, double* xt, double* yt)
{
    if (x>=xt[0] && x<xt[num_pts-1])
        return interpolate(x, xt, yt);
    else
        return extrapolate(x, xt, yt);
}

static double interpolate(double x, double* xt, double* yt)
{
    int i;
    double xa, xb, ya, yb, dx, dy, y;

    for (i=0; i<num_pts-1; ++i)
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

static double extrapolate(double x, double* xt, double* yt)
{
    double dx, dy, y;

    if (x < xt[0]) {
        dx = xt[1] - xt[0];
        dy = yt[1] - yt[0];
        y = yt[0] + (x - xt[0])*dy/dx;
    } else {
        dx = xt[num_pts-1] - xt[num_pts-2];
        dy = yt[num_pts-1] - yt[num_pts-2];
        y = yt[num_pts-1] + (x - xt[num_pts-1])*dy/dx;
    }

    return y;
}

epicsRegisterFunction(ps_conversion_init);
epicsRegisterFunction(ps_conversion_phys2eng_process);
