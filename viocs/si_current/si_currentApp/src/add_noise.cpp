#include <stdio.h>
#include <stdlib.h>
#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

double get_random();

long add_noise(struct aSubRecord *psub)
{
    double *a;
    double *b;
    double *c;
    double noise_level;
    a = (double*) psub->a;
    b = (double*) psub->b;
    c = (double*) psub->c;
    noise_level = c[0];
    for(int i=0; i< psub->noa; i++){
        a[i] = a[i] + get_random()*noise_level*(1e-3);
        b[i] = b[i] + get_random()*noise_level*(1e-3);
    }
    psub->vala = a;
    psub->valb = b;
    return 0;
}

double get_random()
{
    // Return random double between -1.0 and 1.0
    return 2*(double)rand()/RAND_MAX - 1.0;
}

epicsRegisterFunction(add_noise);
