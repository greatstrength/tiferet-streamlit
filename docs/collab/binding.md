# Binding — Tiferet Streamlit

**Project:** Tiferet Streamlit
**Repository:** https://github.com/greatstrength/tiferet-streamlit

This file is the local phone book, not the process. Skills should read `docs/collab/binding.md` in whatever repo they are standing in. If that file is missing, they fall back to the flagship copy at https://github.com/greatstrength/tiferet/blob/main/docs/collab/binding.md, whose process guides (`docs/collab/process.md`, `docs/collab/rfp.md`) are the governing source of truth for this repo too until local copies are added.

## Strands

| Fact | Value |
|---|---|
| Trunk branch | `main` |
| Prototype branch | `v1.x-proto` |
| Prototype strand active | yes |
| RFP id prefix | `STL1` |
| RFP major | `1` |
| Next freeze id pattern | `STL1-FREEZE-<nnn>` |

## GitHub

| Fact | Value |
|---|---|
| Owner / repo | `greatstrength/tiferet-streamlit` |
| Project | Tiferet Framework - Feature Release (#2) |
| Project node id | `PVT_kwDOCKXjws4A7Y85` |

## Project field ids (project #2)

- Status (`PVTSSF_lADOCKXjws4A7Y85zgvs_j4`): Backlog=`f75ad846`, Ready=`08afe404`, In Progress=`47fc9ee4`, In Review=`4cc61d42`, Done=`98236657`
- Priority (`PVTSSF_lADOCKXjws4A7Y85zgvs_no`): P0=`79628723`, P1=`0a877460`, P2=`da944a9c`
- Size (`PVTSSF_lADOCKXjws4A7Y85zgvs_ns`): XS=`eff732af`, S=`9592a5a3`, M=`9728cbdc`, L=`c53df028`, XL=`7b141a16`
- Estimate (`PVTF_lADOCKXjws4A7Y85zgvs_nw`): number
- Start date (`PVTF_lADOCKXjws4A7Y85zgvs_n4`)
- End date (`PVTF_lADOCKXjws4A7Y85zgvs_n8`)

This is the same org-level project shared with sibling repos (e.g. `tiferet-ly`). Field and option ids are unique per GitHub Project, not per repo, so these match the flagship's own binding.md. Re-resolve with `gh project field-list 2 --owner greatstrength --format json` if the project's fields ever change.

## Milestone title shapes

- Prototype drafting round: `vX.Y.0bN`
- Trunk release: `vX.Y.Z`

The first drafting round on this strand is `v1.0.0b1`; its RFPs are what this discovery effort (domain vision, core-domain distillation, and the v1 RFPs) is building toward.
