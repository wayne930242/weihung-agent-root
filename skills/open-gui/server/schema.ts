// Runtime validation for TREE.json against NODE-FORMAT.md's discriminated-union schema.

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

const NODE_TYPES = ["decision", "question", "artifact", "info"] as const;
type NodeType = typeof NODE_TYPES[number];

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function validateNode(node: unknown, index: number, ids: Set<string>): string[] {
  const errors: string[] = [];
  const where = `nodes[${index}]`;

  if (!isPlainObject(node)) {
    return [`${where}: must be an object`];
  }

  if (typeof node.id !== "string" || node.id.length === 0) {
    errors.push(`${where}: id must be a non-empty string`);
  } else {
    ids.add(node.id);
  }

  if (!NODE_TYPES.includes(node.type as NodeType)) {
    errors.push(`${where}: type must be one of ${NODE_TYPES.join(", ")}`);
    return errors; // can't validate type-specific payload without a known type
  }

  if (node.parent !== null && typeof node.parent !== "string") {
    errors.push(`${where}: parent must be a string id or null`);
  }

  if (typeof node.title !== "string" || node.title.length === 0) {
    errors.push(`${where}: title must be a non-empty string`);
  }

  const type = node.type as NodeType;

  if (type === "decision") {
    if (typeof node.recommendation !== "string") {
      errors.push(`${where}: decision nodes require a string recommendation`);
    }
    if (node.status !== "open" && node.status !== "resolved") {
      errors.push(`${where}: decision nodes require status open|resolved`);
    }
    if (node.status === "resolved" && typeof node.resolution !== "string") {
      errors.push(`${where}: resolved decision nodes require a string resolution`);
    }
    if (node.status === "open" && node.resolution !== undefined) {
      errors.push(`${where}: open decision nodes must not have a resolution`);
    }
    if (node.doc !== undefined && typeof node.doc !== "string") {
      errors.push(`${where}: doc, if present, must be a string`);
    }
  } else if (type === "question") {
    if (typeof node.prompt !== "string") {
      errors.push(`${where}: question nodes require a string prompt`);
    }
    if (!Array.isArray(node.options)) {
      errors.push(`${where}: question nodes require an options array`);
    } else {
      for (const [i, opt] of node.options.entries()) {
        if (!isPlainObject(opt) || typeof opt.label !== "string") {
          errors.push(`${where}: options[${i}] requires a string label`);
        }
      }
    }
    if (node.status !== "open" && node.status !== "resolved") {
      errors.push(`${where}: question nodes require status open|resolved`);
    }
    if (node.status === "resolved") {
      const answer = node.answer;
      if (!isPlainObject(answer) || (answer.selectedLabel === undefined && answer.customText === undefined)) {
        errors.push(
          `${where}: resolved question nodes require an answer with selectedLabel and/or customText`,
        );
      }
    }
    if (node.status === "open" && node.answer !== undefined) {
      errors.push(`${where}: open question nodes must not have an answer`);
    }
  } else if (type === "artifact") {
    const kind = node.kind ?? "file";
    if (kind !== "file" && kind !== "url") {
      errors.push(`${where}: artifact kind, if present, must be "file" or "url"`);
    } else if (kind === "file") {
      if (typeof node.path !== "string") {
        errors.push(`${where}: file-kind artifact nodes require a string path`);
      }
      if (node.url !== undefined) {
        errors.push(`${where}: file-kind artifact nodes must not have a url field`);
      }
    } else {
      if (typeof node.url !== "string") {
        errors.push(`${where}: url-kind artifact nodes require a string url`);
      }
      if (node.path !== undefined) {
        errors.push(`${where}: url-kind artifact nodes must not have a path field`);
      }
    }
    if (node.status !== undefined) {
      errors.push(`${where}: artifact nodes must not have a status field`);
    }
  } else if (type === "info") {
    if (typeof node.text !== "string") {
      errors.push(`${where}: info nodes require a string text`);
    }
    if (node.status !== undefined) {
      errors.push(`${where}: info nodes must not have a status field`);
    }
  }

  return errors;
}

export function validateTree(doc: unknown): ValidationResult {
  const errors: string[] = [];

  if (!isPlainObject(doc)) {
    return { valid: false, errors: ["document must be an object"] };
  }

  if (typeof doc.topic !== "string") {
    errors.push("topic must be a string");
  }
  if (doc.status !== "in_progress" && doc.status !== "complete") {
    errors.push("status must be in_progress|complete");
  }
  if (!Array.isArray(doc.nodes)) {
    errors.push("nodes must be an array");
    return { valid: errors.length === 0, errors };
  }

  const ids = new Set<string>();
  doc.nodes.forEach((node, i) => errors.push(...validateNode(node, i, ids)));

  doc.nodes.forEach((node, i) => {
    if (isPlainObject(node) && typeof node.parent === "string" && !ids.has(node.parent)) {
      errors.push(`nodes[${i}]: parent "${node.parent}" does not refer to an existing node id`);
    }
  });

  return { valid: errors.length === 0, errors };
}
