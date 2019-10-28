#!/usr/bin/env python3

"""
Extract RTT metrics from /bin/ip tcp_metrics show
"""

import os, subprocess, time

buckets = [10, 20, 30, 50, 100, 200, 300, 500, 1000]
outfn = "/run/nodeexp/tcp_rtt_ms.prom"

def main():
    cmd = ["/bin/ip", "tcp_metrics", "show"]
    histogram = {t: 0 for t in buckets}
    inf = 0
    _sum = 0
    while True:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in p.stdout:
            line = line.rstrip().decode()
            i = line.find(" rtt ")
            if i == -1:
                continue
            rtt = line[i + 5 :].split(None, 1)[0]
            if not rtt.endswith("us"):
                continue
            rtt = int(rtt[:-2]) / 1000
            _sum += rtt
            for threshold in buckets:
                if rtt <= threshold:
                    # print(rtt, threshold)
                    histogram[threshold] += 1
                    break
            else:
                inf += 1

        f = open(outfn + ".tmp", "w")
        cumulative = 0
        for q, v in sorted(histogram.items()):
            cumulative += v
            print('tcp_rtt_ms_bucket{le="%d"} %d' % (q, cumulative), file=f)
        cumulative += inf
        print('tcp_rtt_ms_bucket{le="+Inf"} %d' % cumulative, file=f)
        # count simply matches the sum of all events
        print("tcp_rtt_ms_count %d" % cumulative, file=f)
        print("tcp_rtt_ms_sum %d" % _sum, file=f)

        f.close()
        os.rename(outfn + ".tmp", outfn)
        time.sleep(3600)


if __name__ == "__main__":
    main()
