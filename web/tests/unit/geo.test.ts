import { describe, expect, it } from "vitest";
import { compassDirection, describePin, distanceMetres, isInsideLondon } from "@/lib/geo";
import { normalisePostcode } from "@/lib/postcode";

const CENTRE = { latitude: 51.5, longitude: -0.12 };

describe("distanceMetres", () => {
  it("measures a thousandth of a degree of latitude as about 111 m", () => {
    const north = { latitude: 51.501, longitude: -0.12 };
    expect(distanceMetres(CENTRE, north)).toBeCloseTo(111.2, 0);
  });
});

describe("compassDirection", () => {
  it.each([
    [0.001, 0, "north"],
    [0, 0.0016, "east"],
    [-0.001, 0, "south"],
    [0.001, -0.0016, "north-west"],
  ])("moving %f, %f is %s", (dLat, dLon, expected) => {
    const to = { latitude: CENTRE.latitude + dLat, longitude: CENTRE.longitude + dLon };
    expect(compassDirection(CENTRE, to)).toBe(expected);
  });
});

describe("describePin", () => {
  it("says when the pin hasn't moved", () => {
    expect(describePin(CENTRE, CENTRE)).toBe("The pin is at the postcode's centre.");
  });

  it("gives a rounded distance and a direction", () => {
    const moved = { latitude: 51.5, longitude: -0.1194 };
    expect(describePin(moved, CENTRE)).toBe("The pin is about 40 m east of the postcode's centre.");
  });

  it("switches to kilometres for longer distances", () => {
    const far = { latitude: 51.515, longitude: -0.12 };
    expect(describePin(far, CENTRE)).toBe(
      "The pin is about 1.7 km north of the postcode's centre.",
    );
  });
});

describe("isInsideLondon", () => {
  it.each([
    ["Trafalgar Square", 51.508, -0.1281, true],
    ["Romford", 51.5768, 0.1801, true],
    ["Reading", 51.4543, -0.9781, false],
    ["Dartford", 51.4462, 0.2169, false],
  ])("knows whether %s is in London", (_, latitude, longitude, expected) => {
    expect(isInsideLondon({ latitude, longitude })).toBe(expected);
  });
});

describe("normalisePostcode", () => {
  it.each([
    ["sw1a 2aa", "SW1A 2AA"],
    ["  SW1A2AA ", "SW1A 2AA"],
    ["e1   6an", "E1 6AN"],
  ])("tidies %s", (text, expected) => {
    expect(normalisePostcode(text)).toBe(expected);
  });

  it.each(["SW1", "hello", "12345", "SW1A 2AA; DROP"])("refuses %s", (text) => {
    expect(normalisePostcode(text)).toBeNull();
  });
});
