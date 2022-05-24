REPLACE INTO objects SET objectId="ZTF20abusqwh", ncand=8,
ramean=59.6143672375,
rastd=0.16665481923539072,
decmean=-8.1728419625,
decstd=0.1307598025961914,
maggmin=20.044300079345703,
maggmax=20.128400802612305,
maggmean=20.07800006866455,
magrmin=20.117080688476562,
magrmax=20.22170066833496,
magrmean=20.157020092010498,
gmag=20.128400802612305,
rmag=20.117080688476562,
dmdt_g=-0.007712665288772353,
dmdt_r=0.001526616611051164,
dmdt_g_err=0.04016815112889961,
dmdt_r_err=0.020087820339961284,
jdgmax=2459265.6506366,
jdrmax=2459276.6365278,
jdmax=2459276.6365278,
jdmin=2459248.7087037,
g_minus_r=-0.06380081176757812,
jd_g_minus_r=2459252.7339931,
glatmean=-41.94209112029505,
glonmean=198.71237942510092,
sgmag1=19.829599380493164,
srmag1=19.61720085144043,
sgscore1=0.9921669960021973,
distpsnr1=0.2525022327899933,
ssnamenr= NULL,
ncandgp=6,
ncandgp_7=1,
ncandgp_14=1,
htm16=37038401653,
mag_g02=20.12809117556159,
mag_g08=20.111518771430696,
mag_g28=20.082909153398912,
mag_r02=20.117083013913255,
mag_r08=20.122688822198818,
mag_r28=20.161621425485386;

REPLACE INTO sherlock_classifications SET classification='VS',
objectId='ZTF20abusqwh',
association_type='VS',
catalogue_table_name='PS1',
catalogue_object_id='98190596143532927',
catalogue_object_type='star',
raDeg='59.614349778',
decDeg='-8.172888384',
separationArcsec='0.24',
northSeparationArcsec='-0.2425824',
eastSeparationArcsec='0.0159571',
physical_separation_kpc='0',
direct_distance='0',
distance='0',
z='0',
photoZ='0',
photoZErr='0',
Mag='19.7',
MagFilter='r',
MagErr='0',
classificationReliability='1',
major_axis_arcsec='5.15',
annotator='https://github.com/thespacedoctor/sherlock/releases/tag/v2.2.0',
additional_output='http://lasair.lsst.ac.uk/api/sherlock/object/ZTF20abusqwh',
description='The transient is synonymous with <em>98190596143532927</em>; an r=19.70 mag stellar source found in the PS1 catalogue. Its located 0.2" from the stellar source core.',
summary='0';

