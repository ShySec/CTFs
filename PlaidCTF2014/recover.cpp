// git clone https://github.com/bwall/HashPump; cd hashpump
// g++ -o recover recover.cpp Extender.cpp MD5ex.cpp -lcrypto -O3
#include <unistd.h>
#include <getopt.h>
#include <openssl/sha.h>
#include "MD5ex.h"

using namespace std;
typedef unsigned char byte;
typedef unsigned long long uint64;

vector<byte> StringToVector(byte * str)
{	// copied from HashPump by Brian Wallace <bwall@openbwall.com>
	vector<byte> ret;
	for(unsigned int x = 0; x < strlen((char*)str); x++)
	{
		ret.push_back(str[x]);
	}
	return ret;
}

void DigestToRaw(string hash, byte * raw)
{	// copied from HashPump by Brian Wallace <bwall@openbwall.com>
	string alpha("0123456789abcdef");
	transform(hash.begin(), hash.end(), hash.begin(), ::tolower);
	for(unsigned int x = 0; x < (hash.length() / 2); x++)
	{
		raw[x] = (byte)((alpha.find(hash.at((x * 2))) << 4));
		raw[x] |= (byte)(alpha.find(hash.at((x * 2) + 1)));
	}
}

void UpdateRawHash(byte *base, byte *raw, uint64 value)
{
	for(int idx=3;idx>=0;idx--)
	{
		raw[idx] = (byte)value;
		value /= 256;
	}
}

void MaskDerivedHash(byte *raw)
{
	raw[3] &= 0x0f;
	raw[0] = raw[1] = raw[2] = 0;
}

void PrintDigest(byte *raw)
{
	for(int i=0;i<16;i++) printf("%02x",raw[i]);
	printf("\n");
}

int main(int argc, char **argv)
{
	if(argc < 5)
	{
		printf("usage: %s <data> <hash> <suffix> <target>\n",argv[0]);
		return 1;
	}
	int keylength = 16;
	char *data = argv[1], *hash = argv[2], *suffix = argv[3], *target = argv[4];

	vector<byte> vmessage = StringToVector((byte*)data);
	vector<byte> vtoadd = StringToVector((byte*)suffix);

	byte hashArr[128]; DigestToRaw(hash, hashArr);
	byte iterArr[128]; memcpy(iterArr,hashArr,sizeof(hashArr));
	byte targetArr[128]; DigestToRaw(target, targetArr);

	Extender *ext = new MD5ex();
	uint64 offset = hashArr[3] & 0x0F; // keep bottom 4 bits
	for(uint64 i=0;i<=(1<<28);i++) // brute forcing top 28 bits
	{
		byte *testArr;
		UpdateRawHash(hashArr, iterArr, (i<<4)+offset);
		delete ext->GenerateStretchedData(vmessage, keylength, iterArr, vtoadd, &testArr);
		MaskDerivedHash(testArr);
		if(memcmp(targetArr,testArr,16))
		{
			delete [] testArr;
			continue;
		}
		PrintDigest(iterArr);
		return 0;
	}
	printf("failed to find hash\n");
}
