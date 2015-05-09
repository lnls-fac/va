/*
 * Conversion of power supply values using excitation tables.
 */


#include <stdio.h>
#include <string.h>

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

#define true 1
#define false 0
#define MAXINTERPTABLESIZE 1000
#define MAXLINESIZE 80


typedef int bool;

static int has_table = false;
static int num_pts = 0;
static double phys[MAXINTERPTABLESIZE], eng[MAXINTERPTABLESIZE];

static bool read_interpolation_table(char* name, double* xt, double* yt);
static double calculate(double x, double* xt, double* yt);
static double interpolate(double x, double* xt, double* yt);
static double extrapolate(double x, double* xt, double* yt);

long ps_conversion_init(struct subRecord *psub)
{
    has_table = read_interpolation_table(psub->name, eng, phys);
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
    FILE* fp;
    char fullname[160] = "/home/fac_files/code/va/viocs/si_ps/si_psApp/src/";

    strcat(fullname, name);
    fp = fopen(fullname, "r");
    if (fp == NULL) {
        printf("Interpolation table for %s not found.\n", name);
        return false;
    } else
        printf("FOUND %s!\n", fullname);


    char line[MAXLINESIZE];
    float x, y;
    int i, n;

    i = 0;
    while(fgets(line, MAXLINESIZE, fp) != NULL) {
        if (line[0] == '#')
            continue;

        n = sscanf(line, "%f %f", &x, &y);
        if (n != 2)
            continue;

        xt[i] = x;
        yt[i] = y;

        i++;
    }

    num_pts = i;

    for (i=0; i<num_pts; ++i)
        printf("x: %7.3f, y: %7.3f\n", xt[i], yt[i]);

    if (num_pts > 0)
        return true;
    else
        return false;
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
