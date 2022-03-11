import argparse
import os
import subprocess
import tempfile
import traceback

from aiohttp import web
import aiohttp


def decompile(path: str) -> str:
    """
    Decompile all the functions in the binary located at `path`.
    """
    logpath = os.path.join(os.getcwd(), 'ida.log')
    subprocess.run(['/opt/ida/idat64', '-A', '-S/opt/ida/decompile_all.py', '-L'+logpath, path])
    try:
        outpath = os.path.join(os.path.dirname(path), 'out.c')
        return open(outpath).read()
    except:
        print(open(logpath).read())


class Service():
    """
    IDA decompiler as a service
    """

    def __init__(self):
        self.app = web.Application()
        self.app.add_routes([web.post('/decompile', self.post_decompile)])

    async def post_decompile(self, request: aiohttp.web.BaseRequest) -> web.Response:
        reader = await request.multipart()
        binary = await reader.next()
        if binary is None:
            return web.Response(status=400)

        with tempfile.NamedTemporaryFile() as f:
            while True:
                chunk = await binary.read_chunk()
                if not chunk:
                    break
                f.write(chunk)
                f.flush()

            try:
                decomp = decompile(f.name)
                resp_status = 200
            except:
                decomp = traceback.format_exc()
                resp_status = 500

            return web.Response(text=decomp, status=resp_status)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?', help='If provided, decompile given file and exit. Otherwise, start server')
    args = ap.parse_args()

    if args.file:
        print(decompile(args.file))
    else:
        s = Service()
        web.run_app(s.app, port=8000)


if __name__ == '__main__':
    main()
