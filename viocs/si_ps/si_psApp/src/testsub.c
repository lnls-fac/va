#include <stdio.h>

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

#define MAXTABSIZE 100


int num_pts;
double xt[MAXTABSIZE], yt[MAXTABSIZE];

double interp(double x);

long testSubInit(struct subRecord *psub)
{
    printf("init was called\n");
    printf("A: %7.3f\n", psub->a);

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

    psub->b = interp(psub->a);

    return 0;
}

double interp(double x)
{
    int i;

    for (i=0; i<num_pts; ++i)
        if (x < xt[i+1])
            break;

    double xa = xt[i];
    double xb = xt[i+1];
    double ya = yt[i];
    double yb = yt[i+1];
    double dx = xb - xa;
    double dy = yb - ya;

    return ya + (x - xa)*dy/dx;
}

epicsRegisterFunction(testSubInit);
epicsRegisterFunction(testSubProcess);
