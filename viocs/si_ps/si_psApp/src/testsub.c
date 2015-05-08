#include <stdio.h>

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

#define MAXTABSIZE 100


int num_pts;
double xt[MAXTABSIZE], yt[MAXTABSIZE];


double calculate(double x);
double interpolate(double x);
double extrapolate(double x);

long testSubInit(struct subRecord *psub)
{
    printf("init was called\n");
    printf("A: %7.3f\n", psub->a);
    printf("Name: %s\n", psub->name);

    num_pts = 20;
    int i;
    for (i=0; i<num_pts; ++i) {
        xt[i] = -10.0 + 20.0*i/num_pts;
        yt[i] = -50.0 + 100.0*i/num_pts;
        printf("x: %7.3f\n", xt[i]);
        printf("y: %7.3f\n", yt[i]);
    }

    return 0;
}

long testSubProcess(struct subRecord *psub)
{
    printf("process was called\n");
    printf("A: %7.3f\n", psub->a);

    psub->b = interpolate(psub->a);

    return 0;
}

double calculate(double x)
{
    if (x>=xt[0] && x<xt[num_pts-1])
        return interpolate(x);
    else
        return extrapolate(x);
}

double interpolate(double x)
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

double extrapolate(double x)
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

epicsRegisterFunction(testSubInit);
epicsRegisterFunction(testSubProcess);
