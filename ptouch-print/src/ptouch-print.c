/*
	ptouch-print - Print labels with images or text on a Brother P-Touch

	Copyright (C) 2015-2024 Dominic Radermacher <dominic@familie-radermacher.ch>

	This program is free software; you can redistribute it and/or modify it
	under the terms of the GNU General Public License version 3 as
	published by the Free Software Foundation

	This program is distributed in the hope that it will be useful, but
	WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
	See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program; if not, write to the Free Software Foundation,
	Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
*/

#include <stdio.h>	/* printf() */
#include <stdlib.h>	/* exit(), malloc() */
#include <stdbool.h>
#include <string.h>	/* strcmp(), memcmp() */
#include <sys/types.h>	/* open() */
#include <sys/stat.h>	/* open() */
#include <fcntl.h>	/* open() */
#include <gd.h>
#include <libintl.h>
#include <locale.h>	/* LC_ALL */

#include "version.h"
#include "gettext.h"	/* gettext(), ngettext() */
#include "ptouch.h"

#define _(s) gettext(s)

#define MAX_LINES 4	/* maybe this should depend on tape size */

gdImage *image_load(const char *file);
void rasterline_setpixel(uint8_t* rasterline, size_t size, int pixel);
int get_baselineoffset(char *text, char *font, int fsz);
int find_fontsize(int want_px, char *font, char *text);
int needed_width(char *text, char *font, int fsz);
int print_img(ptouch_dev ptdev, gdImage *im, int chain);
int write_png(gdImage *im, const char *file);
gdImage *img_append(gdImage *in_1, gdImage *in_2);
gdImage *img_cutmark(int tape_width);
gdImage *render_text(char *font, char *line[], int lines, int tape_width);
void unsupported_printer(ptouch_dev ptdev);
void usage(char *progname);
int parse_args(int argc, char **argv);

// char *font_file = "/usr/share/fonts/TTF/Ubuntu-M.ttf";
// char *font_file = "Ubuntu:medium";
char *font_file = "DejaVuSans";
char *save_png = NULL;
int verbose = 0;
int fontsize = 0;
bool debug = false;
bool chain = false;
int forced_tape_width = 0;

/* --------------------------------------------------------------------
   -------------------------------------------------------------------- */

void rasterline_setpixel(uint8_t* rasterline, size_t size, int pixel)
{
//	TODO: pixel should be unsigned, since we can't have negative
//	if (pixel > ptdev->devinfo->device_max_px) {
	if (pixel > (int)(size*8)) {
		return;
	}
	rasterline[(size-1)-(pixel/8)] |= (uint8_t)(1<<(pixel%8));
	return;
}

int print_img(ptouch_dev ptdev, gdImage *im, int chain)
{
	int d,i,k,offset,tape_width;
	uint8_t rasterline[(ptdev->devinfo->max_px)/8];

	if (!im) {
		printf(_("nothing to print\n"));
		return -1;
	}
	tape_width=ptouch_get_tape_width(ptdev);
	/* find out whether color 0 or color 1 is darker */
	d=(gdImageRed(im,1)+gdImageGreen(im,1)+gdImageBlue(im,1) < gdImageRed(im,0)+gdImageGreen(im,0)+gdImageBlue(im,0))?1:0;
	if (gdImageSY(im) > tape_width) {
		printf(_("image is too large (%ipx x %ipx)\n"), gdImageSX(im), gdImageSY(im));
		printf(_("maximum printing width for this tape is %ipx\n"), tape_width);
		return -1;
	}
	//offset=64-(gdImageSY(im)/2);	/* always print centered */
	size_t max_pixels=ptouch_get_max_width(ptdev);
	offset=((int)max_pixels / 2)-(gdImageSY(im)/2);	/* always print centered */
	printf("max_pixels=%ld, offset=%d\n", max_pixels, offset);
	if ((ptdev->devinfo->flags & FLAG_RASTER_PACKBITS) == FLAG_RASTER_PACKBITS) {
		if (debug) {
			printf("enable PackBits mode\n");
		}
		ptouch_enable_packbits(ptdev);
	}
	if (ptouch_rasterstart(ptdev) != 0) {
		printf(_("ptouch_rasterstart() failed\n"));
		return -1;
	}
	if ((ptdev->devinfo->flags & FLAG_USE_INFO_CMD) == FLAG_USE_INFO_CMD) {
		ptouch_info_cmd(ptdev, gdImageSX(im));
		if (debug) {
			printf(_("send print information command\n"));
		}
	}
	if ((ptdev->devinfo->flags & FLAG_D460BT_MAGIC) == FLAG_D460BT_MAGIC) {
		if (chain) {
			ptouch_send_d460bt_chain(ptdev);
			if (debug) {
				printf(_("send PT-D460BT chain commands\n"));
			}
		}
		ptouch_send_d460bt_magic(ptdev);
		if (debug) {
			printf(_("send PT-D460BT magic commands\n"));
		}
	}
	if ((ptdev->devinfo->flags & FLAG_HAS_PRECUT) == FLAG_HAS_PRECUT) {
		ptouch_send_precut_cmd(ptdev, 1);
		if (debug) {
			printf(_("send precut command\n"));
		}
	}
	for (k=0; k<gdImageSX(im); k+=1) {
		memset(rasterline, 0, sizeof(rasterline));
		for (i=0; i<gdImageSY(im); i+=1) {
			if (gdImageGetPixel(im, k, gdImageSY(im)-1-i) == d) {
				rasterline_setpixel(rasterline, sizeof(rasterline), offset+i);
			}
		}
		if (ptouch_sendraster(ptdev, rasterline, 16) != 0) {
			printf(_("ptouch_sendraster() failed\n"));
			return -1;
		}
	}
	return 0;
}

/* --------------------------------------------------------------------
	Function	image_load()
	Description	detect the type of a image and try to load it
	Last update	2005-10-16
	Status		Working, should add debug info
   -------------------------------------------------------------------- */

gdImage *image_load(const char *file)
{
	const uint8_t png[8]={0x89,'P','N','G',0x0d,0x0a,0x1a,0x0a};
	char d[10];
	FILE *f;
	gdImage *img=NULL;

	if (!strcmp(file, "-")) {
		f = stdin;
	} else {
		f = fopen(file, "rb");
	}
	if (f == NULL) {	/* error could not open file */
		return NULL;
	}
	if (fseek(f, 0L, SEEK_SET)) {	/* file is not seekable. eg 'stdin' */
		img=gdImageCreateFromPng(f);
	} else {
		if (fread(d, sizeof(d), 1, f) != 1) {
			return NULL;
		}
		rewind(f);
		if (memcmp(d, png, 8) == 0) {
			img=gdImageCreateFromPng(f);
		}
	}
	fclose(f);
	return img;
}

int write_png(gdImage *im, const char *file)
{
	FILE *f;

	if ((f = fopen(file, "wb")) == NULL) {
		printf(_("writing image '%s' failed\n"), file);
		return -1;
	}
	gdImagePng(im, f);
	fclose(f);
	return 0;
}

/* --------------------------------------------------------------------
	Find out the difference in pixels between a "normal" char and one
	that goes below the font baseline
   -------------------------------------------------------------------- */
int get_baselineoffset(char *text, char *font, int fsz)
{
	int brect[8];
	int o_offset;
	int text_offset;

	/* NOTE: This assumes that 'o' is always on the baseline */
	gdImageStringFT(NULL, &brect[0], -1, font, fsz, 0.0, 0, 0, "o");
	o_offset=brect[1];
	gdImageStringFT(NULL, &brect[0], -1, font, fsz, 0.0, 0, 0, text);
	text_offset=brect[1];
	if (debug) {
		printf(_("debug: o baseline offset - %d\n"), o_offset);
		printf(_("debug: text baseline offset - %d\n"), text_offset);
	}
	return text_offset-o_offset;
}

/* --------------------------------------------------------------------
	Find out which fontsize we need for a given font to get a
	specified pixel size
	NOTE: This does NOT work for some UTF-8 chars like µ
   -------------------------------------------------------------------- */
int find_fontsize(int want_px, char *font, char *text)
{
	int save=0;
	int brect[8];

	for (int i=4; ; ++i) {
		if (gdImageStringFT(NULL, &brect[0], -1, font, i, 0.0, 0, 0, text) != NULL) {
			break;
		}
		if (brect[1]-brect[5] <= want_px) {
			save=i;
		} else {
			break;
		}
	}
	if (save == 0) {
		return -1;
	}
	return save;
}

int needed_width(char *text, char *font, int fsz)
{
	int brect[8];

	if (gdImageStringFT(NULL, &brect[0], -1, font, fsz, 0.0, 0, 0, text) != NULL) {
		return -1;
	}
	return brect[2]-brect[0];
}

int offset_x(char *text, char *font, int fsz)
{
	int brect[8];

	if (gdImageStringFT(NULL, &brect[0], -1, font, fsz, 0.0, 0, 0, text) != NULL) {
		return -1;
	}
	return -brect[0];
}

gdImage *render_text(char *font, char *line[], int lines, int tape_width)
{
	int brect[8];
	int i, black, x=0, tmp=0, fsz=0;
	char *p;
	gdImage *im=NULL;

	if (debug) {
		printf(_("render_text(): %i lines, font = '%s'\n"), lines, font);
	}
	if (gdFTUseFontConfig(1) != GD_TRUE) {
		printf(_("warning: font config not available\n"));
	}
	if (fontsize > 0) {
		fsz=fontsize;
		printf(_("setting font size=%i\n"), fsz);
	} else {
		for (i=0; i<lines; ++i) {
			if ((tmp=find_fontsize(tape_width/lines, font, line[i])) < 0) {
				printf(_("could not estimate needed font size\n"));
				return NULL;
			}
			if ((fsz == 0) || (tmp < fsz)) {
				fsz=tmp;
			}
		}
		printf(_("choosing font size=%i\n"), fsz);
	}
	for(i=0; i<lines; ++i) {
		tmp=needed_width(line[i], font_file, fsz);
		if (tmp > x) {
			x=tmp;
		}
	}
	im=gdImageCreatePalette(x, tape_width);
	gdImageColorAllocate(im, 255, 255, 255);
	black=gdImageColorAllocate(im, 0, 0, 0);
	/* gdImageStringFT(im,brect,fg,fontlist,size,angle,x,y,string) */
	/* find max needed line height for ALL lines */
	int max_height=0;
	for (i=0; i<lines; ++i) {
		if ((p=gdImageStringFT(NULL, &brect[0], -black, font, fsz, 0.0, 0, 0, line[i])) != NULL) {
			printf(_("error in gdImageStringFT: %s\n"), p);
		}
		//int ofs=get_baselineoffset(line[i], font_file, fsz);
		int lineheight=brect[1]-brect[5];
		if (lineheight > max_height) {
			max_height=lineheight;
		}
	}
	if (debug) {
		printf("debug: needed (max) height is %ipx\n", max_height);
	}
	if ((max_height * lines) > tape_width) {
		printf("Font size %d too large for %d lines\n", fsz, lines);
		return NULL;
	}
	/* calculate unused pixels */
	int unused_px = tape_width - (max_height * lines);
	/* now render lines */
	for (i=0; i<lines; ++i) {
		int ofs=get_baselineoffset(line[i], font_file, fsz);
		//int pos=((i)*(tape_width/(lines)))+(max_height)-ofs-1;
		int pos=((i)*(tape_width/(lines)))+(max_height)-ofs;
		pos += (unused_px/lines) / 2;
		if (debug) {
			printf("debug: line %i pos=%i ofs=%i\n", i+1, pos, ofs);
		}
		int off_x = offset_x(line[i], font_file, fsz);
		if ((p=gdImageStringFT(im, &brect[0], -black, font, fsz, 0.0, off_x, pos, line[i])) != NULL) {
			printf(_("error in gdImageStringFT: %s\n"), p);
		}
	}
	return im;
}

gdImage *img_append(gdImage *in_1, gdImage *in_2)
{
	gdImage *out=NULL;
	int width=0;
	int i_1_x=0;
	int length=0;

	if (in_1 != NULL) {
		width=gdImageSY(in_1);
		length=gdImageSX(in_1);
		i_1_x=gdImageSX(in_1);
	}
	if (in_2 != NULL) {
		length += gdImageSX(in_2);
		/* width should be the same, but let's be sure */
		if (gdImageSY(in_2) > width) {
			width=gdImageSY(in_2);
		}
	}
	if ((width == 0) || (length == 0)) {
		return NULL;
	}
	out=gdImageCreatePalette(length, width);
	if (out == NULL) {
		return NULL;
	}
	gdImageColorAllocate(out, 255, 255, 255);
	gdImageColorAllocate(out, 0, 0, 0);
	if (debug) {
		printf("debug: created new img with size %d * %d\n", length, width);
	}
	if (in_1 != NULL) {
		gdImageCopy(out, in_1, 0, 0, 0, 0, gdImageSX(in_1), gdImageSY(in_1));
		if (debug) {
			printf("debug: copied part 1\n");
		}
	}
	if (in_2 != NULL) {
		gdImageCopy(out, in_2, i_1_x, 0, 0, 0, gdImageSX(in_2), gdImageSY(in_2));
		if (debug) {
			printf("copied part 2\n");
		}
	}
	return out;
}

gdImage *img_cutmark(int tape_width)
{
	gdImage *out=NULL;
	int style_dashed[6];

	out=gdImageCreatePalette(9, tape_width);
	if (out == NULL) {
		return NULL;
	}
	gdImageColorAllocate(out, 255, 255, 255);
	int black=gdImageColorAllocate(out, 0, 0, 0);
	style_dashed[0]=gdTransparent;
	style_dashed[1]=gdTransparent;
	style_dashed[2]=gdTransparent;
	style_dashed[3]=black;
	style_dashed[4]=black;
	style_dashed[5]=black;
	gdImageSetStyle(out, style_dashed, 6);
	gdImageLine(out, 5, 0, 5, tape_width-1, gdStyled);
	return out;
}

gdImage *img_padding(int tape_width, int length)
{
	gdImage *out=NULL;

	if ((length < 1) || (length > 256)) {
		length=1;
	}
	out=gdImageCreatePalette(length, tape_width);
	if (out == NULL) {
		return NULL;
	}
	gdImageColorAllocate(out, 255, 255, 255);
	return out;
}

void usage(char *progname)
{
	printf("usage: %s [options] <print-command(s)>\n", progname);
	printf("options:\n");
	printf("\t--debug\t\t\tenable debug output\n");
	printf("\t--font <file>\t\tuse font <file> or <name>\n");
	printf("\t--fontsize <size>\tManually set fontsize\n");
	printf("\t--writepng <file>\tinstead of printing, write output to png file\n");
	printf("\t--force-tape-width <px>\tSet tape width in pixels, use together with\n");
	printf("\t\t\t\t--writepng without a printer connected.\n");
	printf("\t--copies <number>\tSets the number of identical prints\n");
	printf("print commands:\n");
	printf("\t--image <file>\t\tprint the given image which must be a 2 color\n");
	printf("\t\t\t\t(black/white) png\n");
	printf("\t--text <text>\t\tPrint 1-4 lines of text.\n");
	printf("\t\t\t\tIf the text contains spaces, use quotation marks\n\t\t\t\taround it.\n");
	printf("\t--cutmark\t\tPrint a mark where the tape should be cut\n");
	printf("\t--pad <n>\t\tAdd n pixels padding (blank tape)\n");
	printf("\t--chain\t\t\tSkip final feed of label and any automatic cut\n");
	printf("other commands:\n");
	printf("\t--version\t\tshow version info (required for bug report)\n");
	printf("\t--info\t\t\tshow info about detected tape\n");
	printf("\t--list-supported\tshow printers supported by this version\n");
	exit(1);
}

/* here we don't print anything, but just try to catch syntax errors */
int parse_args(int argc, char **argv)
{
	int lines, i;

	for (i=1; i<argc; ++i) {
		if (*argv[i] != '-') {
			break;
		}
		if (strcmp(&argv[i][1], "-font") == 0) {
			if (i+1<argc) {
				font_file=argv[++i];
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-fontsize") == 0) {
			if (i+1<argc) {
				++i;
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-writepng") == 0) {
			if (i+1<argc) {
				save_png=argv[++i];
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-force-tape-width") == 0) {
			if (i+1<argc) {
				forced_tape_width=strtol(argv[++i], NULL, 10);
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-cutmark") == 0) {
			continue;	/* not done here */
		} else if (strcmp(&argv[i][1], "-chain") == 0) {
			chain=true;
		} else if (strcmp(&argv[i][1], "-debug") == 0) {
			debug=true;
		} else if (strcmp(&argv[i][1], "-info") == 0) {
			continue;	/* not done here */
		} else if (strcmp(&argv[i][1], "-copies") == 0) {
			if (i+1<argc) {
				++i;
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-image") == 0) {
			if (i+1<argc) {
				++i;
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-pad") == 0) {
			if (i+1<argc) {
				++i;
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-text") == 0) {
			for (lines=0; (lines < MAX_LINES) && (i < argc); ++lines) {
				if ((i+1 >= argc) || (argv[i+1][0] == '-')) {
					break;
				}
				++i;
			}
		} else if (strcmp(&argv[i][1], "-version") == 0) {
			printf(_("ptouch-print version %s by Dominic Radermacher\n"), VERSION);
			exit(0);
		} else if (strcmp(&argv[i][1], "-list-supported") == 0) {
			ptouch_list_supported();
			exit(0);
		} else {
			usage(argv[0]);
		}
	}
	if (forced_tape_width && !save_png) {
		forced_tape_width = 0;
	}
	return i;
}

int main(int argc, char *argv[])
{
	int i, lines = 0, tape_width, copies=1;
	char *line[MAX_LINES];
	gdImage *im=NULL;
	gdImage *out=NULL;
	ptouch_dev ptdev=NULL;

	setlocale(LC_ALL, "");
	bindtextdomain("ptouch-print", "/usr/share/locale/");
	textdomain("ptouch-print");
	i=parse_args(argc, argv);
	if (i != argc) {
		usage(argv[0]);
	}
	if (!forced_tape_width) {
		if ((ptouch_open(&ptdev)) < 0) {
			return 5;
		}
		if (ptouch_init(ptdev) != 0) {
			printf(_("ptouch_init() failed\n"));
		}
		if (ptouch_getstatus(ptdev) != 0) {
			printf(_("ptouch_getstatus() failed\n"));
			return 1;
		}
		tape_width=ptouch_get_tape_width(ptdev);
	} else {
		tape_width = forced_tape_width;
	}
	for (i=1; i<argc; ++i) {
		if (*argv[i] != '-') {
			break;
		}
		if (strcmp(&argv[i][1], "-font") == 0) {
			if (i+1<argc) {
				font_file=argv[++i];
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-fontsize") == 0) {
			if (i+1<argc) {
				fontsize=strtol(argv[++i], NULL, 10);
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-force-tape-width") == 0) {
			if (forced_tape_width && save_png) {
				++i;
				continue;
			} else {
				usage(argv[0]);
			}
		} else if (strcmp(&argv[i][1], "-writepng") == 0) {
			i++;
			continue;
		} else if (strcmp(&argv[i][1], "-info") == 0) {
			printf(_("maximum printing width for this tape is %ipx\n"), tape_width);
			printf("media type = %02x (%s)\n", ptdev->status->media_type, pt_mediatype(ptdev->status->media_type));
			printf("media width = %d mm\n", ptdev->status->media_width);
			printf("tape color = %02x (%s)\n", ptdev->status->tape_color, pt_tapecolor(ptdev->status->tape_color));
			printf("text color = %02x (%s)\n", ptdev->status->text_color, pt_textcolor(ptdev->status->text_color));
			printf("error = %04x\n", ptdev->status->error);
			if (debug) {
				ptouch_rawstatus((uint8_t *)ptdev->status);
			}
			exit(0);
		} else if (strcmp(&argv[i][1], "-image") == 0) {
			if ((im=image_load(argv[++i])) == NULL) {
				printf(_("failed to load image file\n"));
				return 1;
			}
			out=img_append(out, im);
			gdImageDestroy(im);
			im = NULL;
		} else if (strcmp(&argv[i][1], "-text") == 0) {
			for (lines=0; (lines < MAX_LINES) && (i < argc); ++lines) {
				if ((i+1 >= argc) || (argv[i+1][0] == '-')) {
					break;
				}
				++i;
				line[lines]=argv[i];
			}
			if (lines) {
				if ((im=render_text(font_file, line, lines, tape_width)) == NULL) {
					printf(_("could not render text\n"));
					return 1;
				}
				out=img_append(out, im);
				gdImageDestroy(im);
				im = NULL;
			}
		} else if (strcmp(&argv[i][1], "-cutmark") == 0) {
			im=img_cutmark(tape_width);
			out=img_append(out, im);
			gdImageDestroy(im);
			im = NULL;
		} else if (strcmp(&argv[i][1], "-pad") == 0) {
			int length=strtol(argv[++i], NULL, 10);
			im=img_padding(tape_width, length);
			out=img_append(out, im);
			gdImageDestroy(im);
			im = NULL;
		} else if (strcmp(&argv[i][1], "-chain") == 0) {
			chain = true;
		} else if (strcmp(&argv[i][1], "-debug") == 0) {
			debug = true;
		} else if (strcmp(&argv[i][1], "-copies") == 0) {
			copies = strtol(argv[++i], NULL, 10);
		} else {
			usage(argv[0]);
		}
	}
	if (out) {
		if (save_png) {
			write_png(out, save_png);
		} else {
			for (i=0; i<copies; ++i) {
				print_img(ptdev, out, chain);
				if (ptouch_finalize(ptdev, ( chain || (i < copies-1) ) ) != 0) {
					printf(_("ptouch_finalize(%d) failed\n"), chain);
					return 2;
				}
			}
		}
		gdImageDestroy(out);
	}
	if (im != NULL) {
		gdImageDestroy(im);
	}
	if (!forced_tape_width) {
		ptouch_close(ptdev);
	}
	libusb_exit(NULL);
	return 0;
}
