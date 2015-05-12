/*
 * Conversion of power supply values using excitation tables.
 */

#include <stdio.h>

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

#include "unit_converter.h"


int num_conversions;
UnitConverter* converter;


long ps_conversion_init(struct subRecord *psub)
{
    num_conversions = psub->a;
    converter = new UnitConverter(psub->name);
    return 0;
}

long ps_conversion_phys2eng_process(struct subRecord *psub)
{
    switch (num_conversions) {
        case 3:
            psub->j = converter->convert_phys2eng(psub->h, psub->i);
        case 2:
            psub->g = converter->convert_phys2eng(psub->e, psub->f);
        case 1:
            psub->d = converter->convert_phys2eng(psub->b, psub->c);
    }

    return 0;
}

long ps_conversion_eng2phys_process(struct subRecord *psub)
{
    switch (num_conversions) {
        case 3:
            psub->j = converter->convert_eng2phys(psub->h, psub->i);
        case 2:
            psub->g = converter->convert_eng2phys(psub->e, psub->f);
        case 1:
            psub->d = converter->convert_eng2phys(psub->b, psub->c);
    }

    return 0;
}


epicsRegisterFunction(ps_conversion_init);
epicsRegisterFunction(ps_conversion_phys2eng_process);
epicsRegisterFunction(ps_conversion_eng2phys_process);
