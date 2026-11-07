// Bezel Charts' elements, so TypeScript knows the attributes this site uses.
import "react";

type BezelAttributes = React.HTMLAttributes<HTMLElement> & {
  values?: string;
  labels?: string;
  min?: string;
  max?: string;
  suffix?: string;
  decimals?: string;
  frame?: "bezel" | "none";
  color?: string;
  background?: string;
  height?: string;
  lang?: string;
};

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "bezel-gauge": BezelAttributes;
    }
  }
}
