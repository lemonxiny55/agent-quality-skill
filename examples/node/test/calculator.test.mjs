import test from "node:test";
import assert from "node:assert/strict";
import { add } from "../src/calculator.mjs";

test("adds positive numbers", () => assert.equal(add(2, 3), 5));
test("adds signed numbers", () => assert.equal(add(-2, 3), 1));
