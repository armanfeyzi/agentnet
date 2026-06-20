import Link from "next/link";

interface FeedPaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
}

function pageHref(page: number): string {
  return page <= 1 ? "/feed" : `/feed?page=${page}`;
}

export function FeedPagination({
  currentPage,
  totalPages,
  totalItems,
}: FeedPaginationProps) {
  if (totalPages <= 1) {
    return (
      <p className="feed-pagination__summary">
        {totalItems} {totalItems === 1 ? "experience" : "experiences"}
      </p>
    );
  }

  const pageNumbers = Array.from({ length: totalPages }, (_, index) => index + 1).filter(
    (page) =>
      page === 1 ||
      page === totalPages ||
      Math.abs(page - currentPage) <= 1,
  );

  const items: Array<number | "ellipsis"> = [];
  for (let index = 0; index < pageNumbers.length; index += 1) {
    const page = pageNumbers[index];
    const previous = pageNumbers[index - 1];

    if (previous !== undefined && page - previous > 1) {
      items.push("ellipsis");
    }

    items.push(page);
  }

  return (
    <nav className="feed-pagination" aria-label="Feed pagination">
      <p className="feed-pagination__summary">
        Page {currentPage} of {totalPages} · {totalItems}{" "}
        {totalItems === 1 ? "experience" : "experiences"}
      </p>

      <div className="feed-pagination__controls">
        {currentPage > 1 ? (
          <Link className="feed-pagination__button" href={pageHref(currentPage - 1)}>
            Previous
          </Link>
        ) : (
          <span className="feed-pagination__button feed-pagination__button--disabled">
            Previous
          </span>
        )}

        <ol className="feed-pagination__pages">
          {items.map((item, index) =>
            item === "ellipsis" ? (
              <li key={`ellipsis-${index}`} className="feed-pagination__ellipsis" aria-hidden>
                …
              </li>
            ) : (
              <li key={item}>
                {item === currentPage ? (
                  <span className="feed-pagination__page feed-pagination__page--current" aria-current="page">
                    {item}
                  </span>
                ) : (
                  <Link className="feed-pagination__page" href={pageHref(item)}>
                    {item}
                  </Link>
                )}
              </li>
            ),
          )}
        </ol>

        {currentPage < totalPages ? (
          <Link className="feed-pagination__button" href={pageHref(currentPage + 1)}>
            Next
          </Link>
        ) : (
          <span className="feed-pagination__button feed-pagination__button--disabled">
            Next
          </span>
        )}
      </div>
    </nav>
  );
}
