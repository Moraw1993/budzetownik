import http2 from "node:http2";
import crypto from "node:crypto";
import { once } from "node:events";
import { setTimeout as sleep } from "node:timers/promises";

const host = process.env.PROXY_HOST;
const repetitions = Number(process.env.PROBE_REPETITIONS || 2);
const expectedHash = crypto.createHash("sha256").update("test").digest("hex");

function complete(result) {
  try {
    const body = JSON.parse(result.body);
    return (
      result.status === 200 &&
      body.id === result.id &&
      body.complete === true &&
      body.received === 4 &&
      body.sha256 === expectedHash
    );
  } catch {
    return false;
  }
}

async function upload(session, port, id, schedule, declared = 4, responseDelay = 0) {
  const started = performance.now();
  const controller = new AbortController();
  const result = {
    id,
    port,
    status: null,
    body: "",
    alpn: session.alpnProtocol,
    queued_bytes: 0,
    send_times: [],
  };
  const request = session.request({
    ":method": "POST",
    ":path": `/api/upload?probe=${id}`,
    ":authority": `localhost:${port}`,
    "content-length": String(declared),
    "x-test-id": id,
    "x-response-delay": String(responseDelay),
  });
  let finalize;
  const completion = new Promise((resolve) => {
    finalize = resolve;
  });
  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    clearTimeout(watchdog);
    result.response_elapsed = (performance.now() - started) / 1000;
    result.rst_code = request.rstCode;
    controller.abort();
    finalize(result);
  };
  request.on("response", (headers) => {
    result.status = Number(headers[":status"]);
    result.response_headers = headers;
    result.headers_elapsed = (performance.now() - started) / 1000;
    controller.abort();
  });
  request.on("data", (chunk) => {
    result.body += chunk;
  });
  request.on("error", (error) => {
    result.response_error = error.code;
    result.response_error_detail = error.message;
  });
  request.on("end", finish);
  request.on("close", finish);
  const watchdog = setTimeout(() => {
    result.local_watchdog = true;
    request.close(http2.constants.NGHTTP2_CANCEL);
    finish();
  }, 12000);

  const sender = (async () => {
    try {
      for (const [at, bytes] of schedule) {
        const remaining = at * 1000 - (performance.now() - started);
        if (remaining > 0) await sleep(remaining, null, { signal: controller.signal });
        if (controller.signal.aborted) break;
        for (let offset = 0; offset < bytes.length; offset += 65536) {
          if (controller.signal.aborted) break;
          const chunk = bytes.subarray(offset, offset + 65536);
          const ready = request.write(chunk);
          result.queued_bytes += chunk.length;
          result.send_times.push((performance.now() - started) / 1000);
          if (!ready) await Promise.race([once(request, "drain"), completion]);
          await sleep(0, null, { signal: controller.signal });
        }
      }
      if (!controller.signal.aborted) request.end();
    } catch (error) {
      if (error.name !== "AbortError") {
        result.send_error = error.code || error.name;
        result.send_error_detail = error.message;
      }
    }
  })();
  await completion;
  await sender;
  if (!request.closed) request.close();
  return result;
}

async function runCase(
  port,
  id,
  schedule,
  { healthy = false, declared = 4, responseDelay = 0 } = {},
) {
  const session = http2.connect(`https://${host}:${port}`, {
    servername: "localhost",
    rejectUnauthorized: false,
  });
  session.on("error", () => {});
  await once(session, "connect");
  if (session.alpnProtocol !== "h2") throw new Error("HTTP/2 ALPN was not negotiated");
  try {
    const sessionStarted = performance.now();
    const pending = upload(session, port, id, schedule, declared, responseDelay);
    const results = [];
    if (healthy) {
      await sleep(1000);
      const healthStarted = performance.now();
      const health = await upload(
        session,
        port,
        `${id}-healthy-stream`,
        [[0, Buffer.from("test")]],
        4,
        1.3,
      );
      health.relative_start = (healthStarted - sessionStarted) / 1000;
      health.relative_end = (performance.now() - sessionStarted) / 1000;
      health.pass = complete(health);
      results.push(health);
    }
    results.push(await pending);
    return results;
  } finally {
    session.destroy();
  }
}

async function main() {
  const results = [];
  const schedules = {
    stalled: [
      [0, Buffer.from("t")],
      [4, Buffer.from("est")],
    ],
    drip: [
      [0, Buffer.from("t")],
      [0.8, Buffer.from("e")],
      [1.6, Buffer.from("s")],
      [2.4, Buffer.from("t")],
    ],
  };
  for (const [name, schedule] of [
    ["quick", [[0, Buffer.from("test")]]],
    [
      "slow-under",
      [
        [0, Buffer.from("t")],
        [0.15, Buffer.from("est")],
      ],
    ],
  ]) {
    const rows = await runCase(8443, `h2-${name}`, schedule);
    rows[0].pass = complete(rows[0]);
    results.push(...rows);
  }
  for (const [name, schedule] of Object.entries(schedules)) {
    const controls = await runCase(8444, `h2-control-${name}`, schedule);
    controls[0].pass = complete(controls[0]);
    results.push(...controls);
    for (let number = 0; number < repetitions; number++) {
      const rows = await runCase(8443, `h2-${name}-${number}`, schedule, { healthy: true });
      const result = rows.at(-1);
      result.pass =
        !result.local_watchdog &&
        ((result.status !== null && !(result.status >= 200 && result.status < 300)) ||
          (result.status === null && result.rst_code !== 0)) &&
        result.response_elapsed >= 1.5 &&
        result.response_elapsed < 3;
      results.push(...rows);
    }
  }
  const length = 26 * 1024 * 1024 + 1;
  const oversize = await runCase(8443, "h2-oversize", [[0, Buffer.alloc(length, "x")]], {
    declared: length,
  });
  oversize[0].pass = oversize[0].status === 413;
  results.push(...oversize);
  if (process.env.REQUIRE_RESPONSE_BUDGET === "1") {
    const boundary = await runCase(
      8443,
      "h2-near-boundary",
      [
        [0, Buffer.from("t")],
        [1.7, Buffer.from("est")],
      ],
      { responseDelay: 0.7 },
    );
    boundary[0].pass =
      boundary[0].status === null &&
      boundary[0].rst_code !== 0 &&
      !boundary[0].local_watchdog &&
      boundary[0].response_elapsed >= 1.5 &&
      boundary[0].response_elapsed < 3.5;
    results.push(...boundary);
  }
  for (const result of results) console.log(JSON.stringify(result));
  process.exitCode = results.every((result) => result.pass) ? 0 : 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
